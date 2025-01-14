"""Platform for sensor integration."""
import logging
from datetime import timedelta

from homeassistant.helpers.entity import Entity

from .configuration import Configuration
from .const import DOMAIN
from .models.kind import BASIC_KINDS, TraktKind

LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN]["instances"]["coordinator"]
    configuration = Configuration(hass.data)

    sensors = []

    for trakt_kind in TraktKind:
        identifier = trakt_kind.value.identifier
        all_medias_possibilities = [False, True]
        for all_medias in all_medias_possibilities:
            if configuration.upcoming_identifier_exists(identifier, all_medias):
                sensor = TraktUpcomingSensor(
                    hass, config_entry, coordinator, trakt_kind, all_medias=all_medias
                )
                sensors.append(sensor)
        if (
            configuration.recommendation_identifier_exists(identifier)
            and trakt_kind in BASIC_KINDS
        ):
            sensor = TraktRecommendationSensor(
                hass, config_entry, coordinator, trakt_kind
            )
            sensors.append(sensor)

    async_add_entities(sensors)


class TraktUpcomingSensor(Entity):
    """Representation of an upcoming sensor."""

    def __init__(self, hass, config_entry, coordinator, trakt_kind, all_medias: bool):
        """Initialize the sensor."""
        self.hass = hass
        self.config_entry = config_entry
        self.coordinator = coordinator
        self.trakt_kind = trakt_kind
        self.all_medias = all_medias

    @property
    def source(self):
        return "all_upcoming" if self.all_medias else "upcoming"

    @property
    def name(self):
        """Return the name of the sensor."""
        prefix = "All " if self.all_medias else ""
        return f"Trakt {prefix}Upcoming {self.trakt_kind.value.name}"

    @property
    def medias(self):
        if self.coordinator.data:
            return self.coordinator.data.get(self.source, {}).get(self.trakt_kind, None)
        return None

    @property
    def configuration(self):
        identifier = self.trakt_kind.value.identifier
        data = self.hass.data[DOMAIN]
        return data["configuration"]["sensors"][self.source][identifier]

    @property
    def data(self):
        if self.medias:
            max_medias = self.configuration["max_medias"]
            return self.medias.to_homeassistant()[0 : max_medias + 1]
        return []

    @property
    def state(self):
        """Return the state of the sensor."""
        return max([len(self.data) - 1, 0])

    @property
    def icon(self):
        """Return the unit of measurement."""
        return "mdi:calendar"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "items"

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {"data": self.data}

    async def async_update(self):
        """Request coordinator to update data."""
        await self.coordinator.async_request_refresh()


class TraktRecommendationSensor(Entity):
    """Representation of a recommendation sensor."""

    def __init__(self, hass, config_entry, coordinator, trakt_kind):
        """Initialize the sensor."""
        self.hass = hass
        self.config_entry = config_entry
        self.coordinator = coordinator
        self.trakt_kind = trakt_kind

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Trakt Recommendation {self.trakt_kind.value.name}"

    @property
    def medias(self):
        if self.coordinator.data:
            return self.coordinator.data.get("recommendation", {}).get(
                self.trakt_kind, None
            )
        return None

    @property
    def configuration(self):
        identifier = self.trakt_kind.value.identifier
        data = self.hass.data[DOMAIN]
        return data["configuration"]["sensors"]["recommendation"][identifier]

    @property
    def data(self):
        if self.medias:
            return self.medias.to_homeassistant()
        return []

    @property
    def state(self):
        """Return the state of the sensor."""
        return max([len(self.data), 0])

    @property
    def icon(self):
        """Return the unit of measurement."""
        return "mdi:movie"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self.trakt_kind.value.path

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {"data": self.data}

    async def async_update(self):
        """Request coordinator to update data."""
        await self.coordinator.async_request_refresh()
