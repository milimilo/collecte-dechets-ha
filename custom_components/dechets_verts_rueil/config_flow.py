"""Config flow : demande l'adresse et détermine le secteur de collecte."""

from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_ADDRESS,
    CONF_LAT,
    CONF_LON,
    DATASET_URL,
    DOMAIN,
    GEOCODE_URL,
)
from .helpers import get_geometry, point_in_geometry


class DechetsVertsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Gère la configuration via l'interface."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS].strip()
            session = async_get_clientsession(self.hass)

            # 1) Géocodage via la Base Adresse Nationale
            try:
                async with session.get(
                    GEOCODE_URL,
                    params={"q": address, "limit": 1},
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as resp:
                    resp.raise_for_status()
                    geo = await resp.json()
            except Exception:  # noqa: BLE001
                errors["base"] = "geocode_error"
            else:
                features = geo.get("features") or []
                if not features:
                    errors[CONF_ADDRESS] = "address_not_found"
                else:
                    lon, lat = features[0]["geometry"]["coordinates"]
                    label = features[0]["properties"].get("label", address)

                    # 2) Vérifie que l'adresse tombe dans un secteur de collecte
                    try:
                        async with session.get(
                            DATASET_URL,
                            params={"limit": 100, "select": "jours,geo_shape"},
                            timeout=aiohttp.ClientTimeout(total=30),
                        ) as resp:
                            resp.raise_for_status()
                            data = await resp.json()
                    except Exception:  # noqa: BLE001
                        errors["base"] = "api_error"
                    else:
                        in_zone = any(
                            point_in_geometry(
                                lon, lat, get_geometry(rec.get("geo_shape"))
                            )
                            for rec in data.get("results", [])
                        )
                        if not in_zone:
                            errors[CONF_ADDRESS] = "outside_zone"
                        else:
                            await self.async_set_unique_id(f"{lat:.5f}_{lon:.5f}")
                            self._abort_if_unique_id_configured()
                            return self.async_create_entry(
                                title=label,
                                data={
                                    CONF_ADDRESS: label,
                                    CONF_LAT: lat,
                                    CONF_LON: lon,
                                },
                            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): str}),
            errors=errors,
        )
