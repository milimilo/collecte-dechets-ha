"""Config flow : saisie d'adresse avec suggestions (Base Adresse Nationale)."""

from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_ADDRESS, CONF_LAT, CONF_LON, DOMAIN, GEOCODE_URL

# Code INSEE de Rueil-Malmaison : restreint les suggestions à la commune,
# ce qui garantit que toute adresse choisie est bien à Rueil.
RUEIL_CITYCODE = "92063"
CONF_CHOICE = "choice"


class CollecteDechetsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configuration en deux étapes : saisie puis confirmation de l'adresse."""

    VERSION = 1

    _query: str = ""
    _suggestions: dict[str, tuple[float, float]] = {}

    async def _search(self, query: str) -> dict[str, tuple[float, float]]:
        """Interroge la Base Adresse Nationale, restreinte à Rueil-Malmaison."""
        session = async_get_clientsession(self.hass)
        async with session.get(
            GEOCODE_URL,
            params={
                "q": query,
                "limit": 10,
                "autocomplete": 1,
                "citycode": RUEIL_CITYCODE,
            },
            timeout=aiohttp.ClientTimeout(total=20),
        ) as resp:
            resp.raise_for_status()
            geo = await resp.json()

        suggestions: dict[str, tuple[float, float]] = {}
        for feat in geo.get("features") or []:
            label = feat.get("properties", {}).get("label")
            coords = feat.get("geometry", {}).get("coordinates")
            if label and coords:
                suggestions[label] = (coords[0], coords[1])
        return suggestions

    def _select_schema(self, query: str) -> vol.Schema:
        labels = list(self._suggestions)
        return vol.Schema(
            {
                vol.Required(CONF_ADDRESS, default=query): str,
                vol.Required(CONF_CHOICE, default=labels[0]): vol.In(labels),
            }
        )

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            query = user_input[CONF_ADDRESS].strip()
            try:
                suggestions = await self._search(query)
            except Exception:  # noqa: BLE001
                errors["base"] = "geocode_error"
            else:
                if not suggestions:
                    errors[CONF_ADDRESS] = "address_not_found"
                else:
                    self._query = query
                    self._suggestions = suggestions
                    return await self.async_step_select()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): str}),
            errors=errors,
        )

    async def async_step_select(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        field_query = self._query

        if user_input is not None:
            new_query = user_input[CONF_ADDRESS].strip()
            field_query = new_query

            if new_query.lower() != self._query.lower():
                # Le champ a été modifié → on relance une recherche.
                try:
                    suggestions = await self._search(new_query)
                except Exception:  # noqa: BLE001
                    errors["base"] = "geocode_error"
                else:
                    if not suggestions:
                        errors[CONF_ADDRESS] = "address_not_found"
                    else:
                        self._query = new_query
                        self._suggestions = suggestions
            else:
                # Texte inchangé → on valide l'adresse choisie.
                # La recherche étant déjà restreinte à Rueil (citycode),
                # aucun contrôle de secteur supplémentaire n'est nécessaire.
                choice = user_input.get(CONF_CHOICE)
                if choice not in self._suggestions:
                    errors[CONF_CHOICE] = "address_not_found"
                else:
                    lon, lat = self._suggestions[choice]
                    await self.async_set_unique_id(f"{lat:.5f}_{lon:.5f}")
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=choice,
                        data={
                            CONF_ADDRESS: choice,
                            CONF_LAT: lat,
                            CONF_LON: lon,
                        },
                    )

        return self.async_show_form(
            step_id="select",
            data_schema=self._select_schema(field_query),
            errors=errors,
        )
