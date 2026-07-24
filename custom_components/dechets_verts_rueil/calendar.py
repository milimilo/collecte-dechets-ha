"""Entité calendrier : affiche les collectes à venir dans le calendrier HA."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, MANUFACTURER
from .coordinator import DechetsVertsCoordinator
from .helpers import dates_in_range

# La collecte a lieu le matin : on crée un créneau 8 h – 12 h.
EVENT_START_HOUR = 8
EVENT_END_HOUR = 12


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DechetsVertsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CollecteCalendar(coordinator, entry)])


class CollecteCalendar(CoordinatorEntity[DechetsVertsCoordinator], CalendarEntity):
    """Calendrier des collectes de déchets verts."""

    _attr_has_entity_name = True
    _attr_translation_key = "collecte"
    _attr_icon = "mdi:calendar-check"

    def __init__(
        self, coordinator: DechetsVertsCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Déchets verts",
            manufacturer=MANUFACTURER,
            model="Collecte des déchets végétaux",
        )

    def _make_event(self, day) -> CalendarEvent:
        start = dt_util.start_of_local_day(day) + timedelta(hours=EVENT_START_HOUR)
        end = dt_util.start_of_local_day(day) + timedelta(hours=EVENT_END_HOUR)
        return CalendarEvent(
            start=start,
            end=end,
            summary="Collecte des déchets verts",
            description="Sortir les déchets végétaux la veille au soir ou tôt le matin.",
        )

    @property
    def event(self) -> CalendarEvent | None:
        upcoming = (self.coordinator.data or {}).get("prochaines") or []
        return self._make_event(upcoming[0]) if upcoming else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        data = self.coordinator.data or {}
        if not data.get("collecte"):
            return []
        days = dates_in_range(
            data.get("jours"),
            data.get("periode"),
            start_date.date(),
            end_date.date(),
        )
        return [self._make_event(day) for day in days]
