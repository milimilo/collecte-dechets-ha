"""Coordinateur : interroge les 5 flux de l'API et détermine le secteur."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ADDRESS,
    CONF_LAT,
    CONF_LON,
    DATASET_URL,
    DOMAIN,
    FLOWS,
)
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

    async def _fetch_flow(
        self, session: aiohttp.ClientSession, key: str, dataset: str
    ) -> dict:
        """Récupère un flux et calcule ses prochaines collectes pour l'adresse."""
        url = DATASET_URL.format(dataset=dataset)
        params = {
            "limit": 100,
            "select": "jours,frequenc,perioann,periojou,geo_shape",
        }
        async with session.get(
            url, params=params, timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

        zone = None
        for record in data.get("results", []):
            geometry = get_geometry(record.get("geo_shape"))
            if point_in_geometry(self.lon, self.lat, geometry):
                zone = record
                break

        if zone is None:
            return {"available": True, "collecte": False, "prochaines": []}

        jours = zone.get("jours")
        frequence = zone.get("frequenc")
        periode = zone.get("perioann")
        collecte = is_collection(jours)
        today = dt_util.now().date()
        upcoming = (
            next_dates(jours, frequence, periode, 6, today) if collecte else []
        )
        return {
            "available": True,
            "collecte": collecte,
            "jours": jours,
            "frequence": frequence,
            "periode": periode,
            "moment": zone.get("periojou"),
            "prochaines": upcoming,
        }

    async def _async_update_data(self) -> dict:
        session = async_get_clientsession(self.hass)
        results = await asyncio.gather(
            *(
                self._fetch_flow(session, key, cfg["dataset"])
                for key, cfg in FLOWS.items()
            ),
            return_exceptions=True,
        )

        flows: dict[str, dict] = {}
        previous = (self.data or {}).get("flows", {})
        failures = 0
        for key, result in zip(FLOWS, results):
            if isinstance(result, Exception):
                failures += 1
                _LOGGER.warning("Flux %s indisponible : %s", key, result)
                # Conserve la dernière valeur connue si elle existe
                flows[key] = previous.get(key, {"available": False, "prochaines": []})
            else:
                flows[key] = result

        if failures == len(FLOWS):
            raise UpdateFailed("Aucun flux joignable sur l'API des Hauts-de-Seine")

        return {"adresse": self.address, "flows": flows}
