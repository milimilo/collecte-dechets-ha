"""Un capteur « prochaine collecte » par flux."""

from __future__ import annotations

from datetime import date

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DEVICE_NAME, DOMAIN, FLOWS, MANUFACTURER
from .coordinator import DechetsVertsCoordinator
from .helpers import relative_label


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DechetsVertsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ProchaineCollecteSensor(coordinator, entry, key, cfg)
        for key, cfg in FLOWS.items()
    )


class ProchaineCollecteSensor(
    CoordinatorEntity[DechetsVertsCoordinator], SensorEntity
):
    """Date de la prochaine collecte pour un flux donné."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(
        self,
        coordinator: DechetsVertsCoordinator,
        entry: ConfigEntry,
        key: str,
        cfg: dict[str, str],
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = cfg["label"]
        self._attr_icon = cfg["icon"]
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=DEVICE_NAME,
            manufacturer=MANUFACTURER,
            model="Collecte des déchets",
            configuration_url="https://opendata.hauts-de-seine.fr/",
        )

    @property
    def _flow(self) -> dict:
        return ((self.coordinator.data or {}).get("flows") or {}).get(self._key, {})

    @property
    def _upcoming(self) -> list[date]:
        return self._flow.get("prochaines") or []

    @property
    def available(self) -> bool:
        return super().available and self._flow.get("available", False)

    @property
    def native_value(self) -> date | None:
        upcoming = self._upcoming
        return upcoming[0] if upcoming else None

    @property
    def extra_state_attributes(self) -> dict:
        flow = self._flow
        upcoming = self._upcoming
        today = dt_util.now().date()
        return {
            "quand": relative_label(upcoming[0], today) if upcoming else "—",
            "collecte": flow.get("collecte", False),
            "jour": flow.get("jours"),
            "frequence": flow.get("frequence"),
            "periode": flow.get("periode"),
            "moment": flow.get("moment"),
            "adresse": (self.coordinator.data or {}).get("adresse"),
            "jours_avant": (upcoming[0] - today).days if upcoming else None,
            "prochaines_collectes": [d.isoformat() for d in upcoming],
        }
