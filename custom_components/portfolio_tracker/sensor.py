"""Sensors for an investment portfolio."""

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PortfolioCoordinator
from .models import Holding, Quote, calculate_total


class HoldingSensor(CoordinatorEntity[PortfolioCoordinator], SensorEntity):
    """Price or market value sensor for one holding."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_has_entity_name = True
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: PortfolioCoordinator,
        entry: ConfigEntry,
        holding: Holding,
        metric: str,
    ) -> None:
        """Initialize a holding sensor."""
        super().__init__(coordinator)
        self.holding = holding
        self.metric = metric
        self._attr_name = f"{holding.symbol} {metric.replace('_', ' ').title()}"
        self._attr_native_unit_of_measurement = coordinator.currency
        self._attr_unique_id = (
            f"{entry.entry_id}_{holding.symbol.lower()}_{metric}"
        )
        self._attr_state_class = (
            SensorStateClass.TOTAL if metric == "market_value" else None
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Investment Portfolio",
            manufacturer="Yahoo Finance",
        )

    @property
    def native_value(self) -> float | None:
        """Return the price or market value for this holding."""
        quote = self.coordinator.data.get(self.holding.symbol)
        if quote is None or quote.currency != self.coordinator.currency:
            return None
        value = quote.price
        if self.metric == "market_value":
            value *= self.holding.quantity
        return float(value)

    @property
    def available(self) -> bool:
        """Report a holding as unavailable when its quote cannot be valued."""
        return super().available and self.native_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose holding details and quote freshness."""
        quote = self.coordinator.data.get(self.holding.symbol)
        attributes: dict[str, Any] = {
            "symbol": self.holding.symbol,
            "quantity": str(self.holding.quantity),
            "currency": (
                quote.currency if quote is not None else self.coordinator.currency
            ),
        }
        if quote and quote.timestamp:
            attributes["quote_updated_at"] = quote.timestamp.isoformat()
        return attributes


class PortfolioTotalSensor(CoordinatorEntity[PortfolioCoordinator], SensorEntity):
    """Total portfolio market value sensor."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_has_entity_name = True
    _attr_name = "Total Value"
    _attr_suggested_display_precision = 2
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self, coordinator: PortfolioCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the portfolio total sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_total_value"
        self._attr_native_unit_of_measurement = coordinator.currency
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Investment Portfolio",
            manufacturer="Yahoo Finance",
        )

    @property
    def native_value(self) -> float | None:
        """Return the total only when every holding has a usable quote."""
        total = calculate_total(
            self.coordinator.holdings,
            self.coordinator.data,
            self.coordinator.currency,
        )
        return float(total) if total is not None else None

    @property
    def available(self) -> bool:
        """Report the total as unavailable unless all holdings can be valued."""
        return super().available and self.native_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose portfolio currency and holding count."""
        return {
            "currency": self.coordinator.currency,
            "holding_count": len(self.coordinator.holdings),
        }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up portfolio sensors and remove obsolete holding entities."""
    coordinator: PortfolioCoordinator = hass.data[DOMAIN][entry.entry_id]
    unique_ids = {f"{entry.entry_id}_total_value"}
    entities: list[SensorEntity] = [PortfolioTotalSensor(coordinator, entry)]

    for holding in coordinator.holdings:
        for metric in ("price", "market_value"):
            unique_ids.add(f"{entry.entry_id}_{holding.symbol.lower()}_{metric}")
            entities.append(HoldingSensor(coordinator, entry, holding, metric))

    registry = er.async_get(hass)
    for entity in list(registry.entities.values()):
        if (
            entity.config_entry_id == entry.entry_id
            and entity.platform == DOMAIN
            and entity.unique_id.startswith(f"{entry.entry_id}_")
            and entity.unique_id not in unique_ids
        ):
            registry.async_remove(entity.entity_id)

    async_add_entities(entities)
