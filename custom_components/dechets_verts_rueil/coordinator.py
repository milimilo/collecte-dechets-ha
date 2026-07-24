"""Coordinateur : récupère les données de l'API et détermine le secteur."""

from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import CONF_ADDRESS, CONF_LAT, CONF_LON, DATASET_URL, DOMAIN
from .helpers import get_geometry, is_collection, next_dates, point_in_geometry

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(hours=12)


class DechetsVertsCoordinator(DataUpdateCoordinator):
    """Interroge l'API des Hauts-de-Seine et calcule les prochaines collectes."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.entry = entry
        self.lat: float = entry.data[CONF_LAT]
        self.lon: float = entry.data[CONF_LON]
        self.address: str = entry.data[CONF_ADDRESS]

    async def _async_update_data(self) -> dict:
        session = async_get_clientsession(self.hass)
        params = {
            "limit": 100,
            "select": "jours,frequenc,perioann,periojou,geo_shape",
        }
        try:
            async with session.get(
                DATASET_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Erreur API Hauts-de-Seine : {err}") from err

        zone = None
        for record in data.get("results", []):
            geometry = get_geometry(record.get("geo_shape"))
            if point_in_geometry(self.lon, self.lat, geometry):
                zone = record
                break

        if zone is None:
            return {
                "found": False,
                "adresse": self.address,
                "collecte": False,
                "prochaines": [],
            }

        jours = zone.get("jours")
        collecte = is_collection(jours)
        today = dt_util.now().date()
        upcoming = next_dates(jours, zone.get("perioann"), 6, today) if collecte else []

        return {
            "found": True,
            "collecte": collecte,
            "jours": jours,
            "frequence": zone.get("frequenc"),
            "periode": zone.get("perioann"),
            "moment": zone.get("periojou"),
            "adresse": self.address,
            "prochaines": upcoming,
        }
