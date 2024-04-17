# Object Location Tones
# A global plugin for NVDA
# Copyright 2017-2024 Joseph Lee, released under GPL
# Copyright      2024  Dalen Bernaca, released under GPL

# Brings NVDA Core issue 2559 to life.

import globalPluginHandler
import scriptHandler

import config
import ui

from tones import beep
from api import getDesktopObject, getNavigatorObject
from textInfos import POSITION_CARET
from winUser import getCursorPos
from controlTypes import ROLE_TERMINAL, ROLE_EDITABLETEXT, ROLE_PASSWORDEDIT

minPitch  = config.conf['mouse']['audioCoordinates_minPitch']
maxPitch  = config.conf['mouse']['audioCoordinates_maxPitch']
maxVolume = config.conf['mouse']['audioCoordinates_maxVolume']

def isEditable (obj):
    r = obj.role
    return r==ROLE_EDITABLETEXT or r==ROLE_PASSWORDEDIT or r==ROLE_TERMINAL

class GlobalPlugin (globalPluginHandler.GlobalPlugin):
    def __init__ (self):
        super(globalPluginHandler.GlobalPlugin, self).__init__()
        self.duration   = 40
        self.volume     = maxVolume
        self.stereoSwap = False
        self.focusing = True # A flag to prevent double beeps on focus of text area children
        self.event_becomeNavigatorObject = self._on_becomeNavigatorObject
        self.event_caret = self._on_caret

    def playCoordinates (self, x, y, d=None):
        """
        Plays a positional tone for given x and y coordinates,
        relative to current desktop window size.
        """
        screenWidth, screenHeight = getDesktopObject().location[2:]
        if 0 <= x <= screenWidth and 0 <= y <= screenHeight:
            curPitch = minPitch + ((maxPitch - minPitch) * ((screenHeight - y) / float(screenHeight)))
            if self.stereoSwap:
                rightVolume = int((85 * ((screenWidth - float(x)) / screenWidth)) * self.volume)
                leftVolume = int((85 * (float(x) / screenWidth)) * self.volume)
            else: 
                leftVolume = int((85 * ((screenWidth - float(x)) / screenWidth)) * self.volume)
                rightVolume = int((85 * (float(x) / screenWidth)) * self.volume)
            beep(curPitch, (d or self.duration), left=leftVolume, right=rightVolume)

    @scriptHandler.script(
        # Translators: Input dialog gesture description for on request of mouse cursor location
        description=_("Play a positional tone for a mouse cursor"),
        # Translators: Input gestures dialog category for objLocTones.
        category=_("Object Location Tones") )
    def script_mouse (self, gesture):
        try:
            x, y = getCursorPos()
            self.playCoordinates(x, y, self.duration+50)
        except:
            pass

    @scriptHandler.script(
        # Translators: The gesture description for on request object location in the input gesture dialog
        description=_("Play a positional tone for the current navigator object"),
        # Translators: Input gestures dialog category for objLocTones.
        category=_("Object Location Tones") )
    def script_locate (self, gesture):
        obj = getNavigatorObject()
        if isEditable(obj):
            try:
                tei = obj.makeTextInfo(POSITION_CARET)
                x, y = tei.pointAtStart
                self.playCoordinates(x+3, y+8, self.duration+30)
            except:
                pass
            return
        try:
            l, t, w, h = obj.location
            x = l + (w // 2)
            y = t + (h // 2)
            self.playCoordinates(x, y, self.duration+30)
        except:
            pass

    @scriptHandler.script(
        # Translators: The toggle gesture description in the input gesture dialog
        description=_("Toggle automatic auditory description of object locations via positional tones."),
        # Translators: Input gestures dialog category for objLocTones.
        category=_("Object Location Tones") )
    def script_toggle (self, gesture):
        """
        Toggles positional tones on or off by swapping
        relevant event handlers accordingly.
        """
        if self.event_becomeNavigatorObject==self._on_passThrough:
            self.event_becomeNavigatorObject = self._on_becomeNavigatorObject
            self.event_caret = self._on_caret
            self.focusing = True
            # Translators: Message when positional tones are switched on
            ui.message(_("Positional tones on"))
            return
        self.event_becomeNavigatorObject = self._on_passThrough
        self.event_caret = self._on_passThrough
        # Translators: Message when positional tones are switched off
        ui.message(_("Positional tones off"))

    def _on_passThrough (self, obj, nextHandler, *args, **kwargs):
        """
        An event handler that just passes the event to the next handler and does nothing else.
        Used to swap a real handler when switching off a feature.
        """
        nextHandler()

    def _on_becomeNavigatorObject (self, obj, nextHandler, *args, **kwargs):
        """
        Event handler that plays a positional tone upon navigation.
        """
        self.focusing = True # Prevent beep of the caret event right after text area gains focus
        try:
            l, t, w, h = obj.location
            x = l + (w // 2)
            y = t + (h // 2)
            self.playCoordinates(x, y)
        except:
            pass
        nextHandler()

    event_becomeNavigatorObject = _on_becomeNavigatorObject

    def _on_caret (self, obj, nextHandler):
        """
        Event handler that plays a positional tone upon caret movements.
        """
        if self.focusing:
            # Skip a beep right after text area gained focus
            self.focusing = False
            nextHandler()
            return
        if obj.role==ROLE_TERMINAL:
            nextHandler()
            return
        try:
            tei = obj.makeTextInfo(POSITION_CARET)
            x, y = tei.pointAtStart
            self.playCoordinates(x+3, y+8)
        except:
            pass
        nextHandler()

    event_caret = _on_caret
