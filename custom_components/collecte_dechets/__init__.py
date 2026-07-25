"""Intégration Collecte des déchets Rueil-Malmaison."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_change

from .const import DOMAIN
from .coordinator import DechetsVertsCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.CALENDAR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configure une entrée depuis l'interface."""
    coordinator = DechetsVertsCoordinator(hass, entry)
    # Refresh non bloquant : les entités sont créées même si l'API ne répond
    # pas au démarrage (elles apparaîtront « indisponible » puis se rempliront).
    await coordinator.async_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # Rafraîchissement à minuit (heure locale) : les libellés « Aujourd'hui /
    # Demain » et la prochaine date doivent basculer pile au changement de jour.
    async def _refresh_at_midnight(_now) -> None:
        await coordinator.async_request_refresh()

    entry.async_on_unload(
        async_track_time_change(
            hass, _refresh_at_midnight, hour=0, minute=0, second=1
        )
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharge une entrée."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Recharge l'intégration après modification des options."""
    await hass.config_entries.async_reload(entry.entry_id)
