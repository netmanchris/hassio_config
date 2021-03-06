Skip to content
Why GitHub? 
Enterprise
Explore 
Marketplace
Pricing 
Search

Sign in
Sign up
65 175 77 keatontaylor/alexa_media_player
 Code  Issues 11  Pull requests 0  Projects 1  Wiki  Insights
Join GitHub today
GitHub is home to over 31 million developers working together to host and review code, manage projects, and build software together.

alexa_media_player/alexa_media/notify.py
@alandtse alandtse Fix bug where any invalid target would stop service call
b2ec297 19 days ago
182 lines (162 sloc)  7.25 KB
    
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  SPDX-License-Identifier: Apache-2.0
"""
Alexa Devices notification service.
For more details about this platform, please refer to the documentation at
https://community.home-assistant.io/t/echo-devices-alexa-as-media-player-testers-needed/58639
"""
import logging

from homeassistant.components.notify import (
    ATTR_DATA, ATTR_TARGET, ATTR_TITLE, ATTR_TITLE_DEFAULT,
    BaseNotificationService
)

from . import (
        DOMAIN as ALEXA_DOMAIN,
        DATA_ALEXAMEDIA,
        hide_email, hide_serial)

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [ALEXA_DOMAIN]

EVENT_NOTIFY = "notify"


def get_service(hass, config, discovery_info=None):
    # pylint: disable=unused-argument
    """Get the demo notification service."""
    return AlexaNotificationService(hass)


class AlexaNotificationService(BaseNotificationService):
    """Implement Alexa Media Player notification service."""

    def __init__(self, hass):
        """Initialize the service."""
        self.hass = hass

    def convert(self, names, type_="entities", filter_matches=False):
        """Return a list of converted Alexa devices based on names.
        Names may be matched either by serialNumber, accountName, or
        Homeassistant entity_id and can return any of the above plus entities
        Parameters
        ----------
        names : list(string)
            A list of names to convert
        type : string
            The type to return entities, entity_ids, serialnumbers, names
        filter_matches : bool
            Whether non-matching items are removed from the returned list.
        Returns
        -------
        list(string)
            List of home assistant entity_ids
        """
        devices = []
        if isinstance(names, str):
            names = [names]
        for item in names:
            matched = False
            for alexa in self.devices:
                _LOGGER.debug("Testing item: %s against (%s, %s, %s, %s)",
                              item,
                              alexa,
                              alexa.name,
                              hide_serial(alexa.unique_id),
                              alexa.entity_id)
                if item in (alexa, alexa.name, alexa.unique_id,
                            alexa.entity_id):
                    if type_ == "entities":
                        converted = alexa
                    elif type_ == "serialnumbers":
                        converted = alexa.unique_id
                    elif type_ == "names":
                        converted = alexa.name
                    elif type_ == "entity_ids":
                        converted = alexa.entity_id
                    devices.append(converted)
                    matched = True
                    _LOGGER.debug("Converting: %s to (%s): %s",
                                  item,
                                  type_,
                                  converted)
            if not filter_matches and not matched:
                devices.append(item)
        return devices

    # This can't be enabled because notify is setup before the media_player
    # once a method is determined to wait till media_player, this can be used
    # @property
    # def targets(self):
    #     """Return a dictionary of Alexa devices."""
    #     devices = {}
    #     # if ('accounts' not in self.hass.data[DATA_ALEXAMEDIA] or
    #     #         self.hass.data[DATA_ALEXAMEDIA]['accounts'].items()):
    #     #     return devices
    #     for account, account_dict in (self.hass.data[DATA_ALEXAMEDIA]
    #                                   ['accounts'].items()):
    #         for alexa in account_dict['entities']['media_player'].values():
    #             devices[alexa.name] = alexa
    #         _LOGGER.debug("Account: %s Devices: %s Raw:%s",
    #                       hide_email(account),
    #                       devices,
    #                       account_dict)
    #     return devices

    @property
    def devices(self):
        """Return a dictionary of Alexa devices."""
        devices = []
        if ('accounts' not in self.hass.data[DATA_ALEXAMEDIA] and
                not self.hass.data[DATA_ALEXAMEDIA]['accounts'].items()):
            return devices
        for _, account_dict in (self.hass.data[DATA_ALEXAMEDIA]
                                ['accounts'].items()):
            devices = devices + list(account_dict
                                     ['entities']['media_player'].values())
        return devices

    def send_message(self, message="", **kwargs):
        """Send a message to a Alexa device."""
        _LOGGER.info("Message: %s, kwargs: %s",
                     message,
                     kwargs)
        kwargs['message'] = message
        targets = kwargs.get(ATTR_TARGET)
        title = (kwargs.get(ATTR_TITLE) if ATTR_TITLE in kwargs
                 else ATTR_TITLE_DEFAULT)
        data = kwargs.get(ATTR_DATA)
        if isinstance(targets, str):
            targets = [targets]
        entities = self.convert(targets, type_="entities")
        try:
            entities.extend(self.hass.components.group.expand_entity_ids(
                entities))
        except ValueError:
            _LOGGER.info("Invalid Home Assistant entity in %s", entities)
        if data['type'] == "tts":
            targets = self.convert(entities, type_="entities",
                                   filter_matches=True)
            _LOGGER.debug("TTS entities: %s", targets)
            for alexa in targets:
                _LOGGER.info("TTS by %s : %s", alexa, message)
                alexa.send_tts(message)
        elif data['type'] == "announce":
            targets = self.convert(entities, type_="serialnumbers",
                                   filter_matches=True)
            _LOGGER.debug("Announce targets: %s entities: %s",
                          list(map(hide_serial, targets)),
                          entities)
            for account, account_dict in (self.hass.data[DATA_ALEXAMEDIA]
                                          ['accounts'].items()):
                for alexa in (account_dict['entities']
                              ['media_player'].values()):
                    if alexa.unique_id in targets and alexa.available:
                        _LOGGER.info(("%s: Announce by %s to "
                                      "targets: %s: %s"),
                                     hide_email(account),
                                     alexa,
                                     list(map(hide_serial, targets)),
                                     message)
                        alexa.send_announcement(message,
                                                targets=targets,
                                                title=title,
                                                method=(data['method'] if
                                                        'method' in data
                                                        else 'all'))
                        break
        elif data['type'] == "push":
            targets = self.convert(entities, type_="entities",
                                   filter_matches=True)
            for alexa in targets:
                _LOGGER.info("Push by %s : %s %s", alexa, title, message)
                alexa.send_mobilepush(message, title=title)
© 2019 GitHub, Inc.
Terms
Privacy
Security
Status
Help
Contact GitHub
Pricing
API
Training
Blog
About
