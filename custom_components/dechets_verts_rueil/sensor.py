"""Capteurs : prochaine collecte et nombre de jours avant."""

from __future__ import annotations

from datetime import date

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, MANUFACTURER
from .coordinator import DechetsVertsCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DechetsVertsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ProchaineCollecteSensor(coordinator, entry),
            JoursAvantSensor(coordinator, entry),
        ]
    )


class _BaseSensor(CoordinatorEntity[DechetsVertsCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: DechetsVertsCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Déchets verts",
            manufacturer=MANUFACTURER,
            model="Collecte des déchets végétaux",
            configuration_url="https://opendata.hauts-de-seine.fr/",
        )

    @property
    def _upcoming(self) -> list[date]:
        return (self.coordinator.data or {}).get("prochaines") or []


class ProchaineCollecteSensor(_BaseSensor):
    """Date de la prochaine collecte."""

    _attr_translation_key = "prochaine_collecte"
    _attr_icon = "mdi:leaf"
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_prochaine_collecte"

    @property
    def native_value(self) -> date | None:
        upcoming = self._upcoming
        return upcoming[0] if upcoming else None

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data or {}
        upcoming = self._upcoming
        today = dt_util.now().date()
        return {
            "secteur_avec_collecte": data.get("collecte", False),
            "jour": data.get("jours"),
            "frequence": data.get("frequence"),
            "periode": data.get("periode"),
            "moment": data.get("moment"),
            "adresse": data.get("adresse"),
            "jours_avant": (upcoming[0] - today).days if upcoming else None,
            "prochaines_collectes": [d.isoformat() for d in upcoming],
        }


class JoursAvantSensor(_BaseSensor):
    """Nombre de jours avant la prochaine collecte."""

    _attr_translation_key = "jours_avant"
    _attr_icon = "mdi:calendar-clock"
    _attr_native_unit_of_measurement = "j"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_jours_avant"

    @property
    def native_value(self) -> int | None:
        upcoming = self._upcoming
        if not upcoming:
            return None
        return (upcoming[0] - dt_util.now().date()).days
