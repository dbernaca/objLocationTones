# Object Location Tones
# A global plugin for NVDA
# Copyright 2017-2024 Joseph Lee, released under GPL
# Copyright      2024  Dalen Bernaca, released under GPL

# Brings NVDA Core issue 2559 to life.

import globalPluginHandler
import scriptHandler

import tones
import config
import api
import ui

minPitch  = config.conf['mouse']['audioCoordinates_minPitch']
maxPitch  = config.conf['mouse']['audioCoordinates_maxPitch']
maxVolume = config.conf['mouse']['audioCoordinates_maxVolume']

class GlobalPlugin (globalPluginHandler.GlobalPlugin):
    def __init__ (self):
        super(globalPluginHandler.GlobalPlugin, self).__init__()
        self.event_becomeNavigatorObject = self._on_becomeNavigatorObject

    @scriptHandler.script(
        # Translators: The gesture description in the input gesture dialog
        description=_("Toggles automatic auditory description of object locations via positional tones."),
        # Translators: Input gestures dialog category for objLocTones.
        category=_("Object Location Tones") )
    def script_toggle (self, gesture):
        if self.event_becomeNavigatorObject==self._on_passThrough:
            self.event_becomeNavigatorObject = self._on_becomeNavigatorObject
            # Translators: Message when positional tones are switched on
            ui.message(_("Positional tones on"))
            return
        self.event_becomeNavigatorObject = self._on_passThrough
        # Translators: Message when positional tones are switched off
        ui.message(_("Positional tones off"))

    def _on_passThrough (self, obj, nextHandler, *args, **kwargs):
        nextHandler()

    def _on_becomeNavigatorObject (self, obj, nextHandler, *args, **kwargs):
        # Until NVDA Core 2559 is implemented...
        try:
            l, t, w, h = obj.location
            x = l + (w // 2)
            y = t + (h // 2)
            screenWidth, screenHeight = api.getDesktopObject().location[2:]
            if 0 <= x <= screenWidth and 0 <= y <= screenHeight:
                curPitch = minPitch + ((maxPitch - minPitch) * ((screenHeight - y) / float(screenHeight)))
                leftVolume = int((85 * ((screenWidth - float(x)) / screenWidth)) * maxVolume)
                rightVolume = int((85 * (float(x) / screenWidth)) * maxVolume)
                tones.beep(curPitch, 40, left=leftVolume, right=rightVolume)
        except TypeError:
            pass
        nextHandler()

    event_becomeNavigatorObject = _on_becomeNavigatorObject