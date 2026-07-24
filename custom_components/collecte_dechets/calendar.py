"""Calendrier unique regroupant les collectes de tous les flux."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DEVICE_NAME, DOMAIN, FLOWS, MANUFACTURER
from .coordinator import DechetsVertsCoordinator
from .helpers import dates_in_range

# Collecte le matin ou le soir : on pose un créneau indicatif.
SLOTS = {
    "matin": (7, 11),
    "soir": (18, 21),
}
DEFAULT_SLOT = (7, 11)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DechetsVertsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CollecteCalendar(coordinator, entry)])


class CollecteCalendar(CoordinatorEntity[DechetsVertsCoordinator], CalendarEntity):
    """Calendrier de toutes les collectes de déchets."""

    _attr_has_entity_name = True
    _attr_name = "Collectes"
    _attr_icon = "mdi:calendar-check"

    def __init__(
        self, coordinator: DechetsVertsCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=DEVICE_NAME,
            manufacturer=MANUFACTURER,
            model="Collecte des déchets",
        )

    def _make_event(self, day, label: str, moment: str | None) -> CalendarEvent:
        slot = SLOTS.get((moment or "").strip().lower(), DEFAULT_SLOT)
        base = dt_util.start_of_local_day(day)
        return CalendarEvent(
            start=base + timedelta(hours=slot[0]),
            end=base + timedelta(hours=slot[1]),
            summary=f"Collecte : {label}",
            description=(
                f"Collecte {label.lower()} le {moment.lower() if moment else 'matin'}."
            ),
        )

    def _next_event_for(self, key: str, flow: dict) -> CalendarEvent | None:
        upcoming = flow.get("prochaines") or []
        if not upcoming:
            return None
        return self._make_event(upcoming[0], FLOWS[key]["label"], flow.get("moment"))

    @property
    def event(self) -> CalendarEvent | None:
        flows = (self.coordinator.data or {}).get("flows") or {}
        candidates = [
            ev
            for key, flow in flows.items()
            if (ev := self._next_event_for(key, flow)) is not None
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda ev: ev.start)

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        flows = (self.coordinator.data or {}).get("flows") or {}
        events: list[CalendarEvent] = []
        for key, flow in flows.items():
            if not flow.get("collecte"):
                continue
            days = dates_in_range(
                flow.get("jours"),
                flow.get("frequence"),
                flow.get("periode"),
                start_date.date(),
                end_date.date(),
            )
            label = FLOWS[key]["label"]
            moment = flow.get("moment")
            events.extend(self._make_event(day, label, moment) for day in days)
        events.sort(key=lambda ev: ev.start)
        return events
