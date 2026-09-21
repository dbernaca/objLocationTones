# Part of Object Location Tones add-on
# This module implementsa a kind of mixin class that is a part of the GlobalPlugin()
# Its content should be viewed as a continuation of that class from __init__.py
# Methods that are used to turn add-on features off and on are hosted here
# because the add-ons main class is getting too large for simple maintenance
# and needs some clearing. So, gesture handling script methods are being separated into a mixin style class in their own module.

from .constants import IS_LOCATION_MODE_NAVIGATOR
from .          import dependencies as deps
from .utils     import getForegroundObject
from .posTones  import playCoordinates
from .          import posTones
from .UIStrings import DLG_WARN_EXPERIMENTAL, DLG_WARN
from logHandler import log
import inputCore
import gui
import wx

__all__ = ["_objlocSwitchMethods"]

class _objlocSwitchMethods:
    """
    This class is mixed into GlobalPlugin() via inheritance and implements methods used to toggle features.
    Methods are used either by a script, or a settings panel element or both.
    Some of them are prepared to act both as reactor and retractor callbacks
    so that the settings panel can support interactive feature changes and
    that discarding choices upon using the cancel button works properly.
    Some of them can also be called directly from a script, to change features using a gesture.
    """
    def Activate (self):
        if IS_LOCATION_MODE_NAVIGATOR(self.locationMode):
            self.event_becomeNavigatorObject = self._on_navigation
        else:
            self.event_gainFocus = self._on_navigation
        if self.caret:
            self.ActivateCaret()
        if self.easyTableNav:
            deps.enableAddonSupport("easyTableNavigator", onNavigation=self._on_easyTableNav)
        if self.reportOutline:
            self.event_foreground = self._on_foreground
        else:
            self.event_foreground = self._on_passThrough
        self.focusing = True
        self.typing = False

    def Deactivate (self):
        self.event_becomeNavigatorObject = self._on_passThrough
        self.event_gainFocus  = self._on_passThrough
        self.event_foreground = self._on_passThrough
        self.DeactivateCaret()
        if self.easyTableNav:
            deps.disableAddonSupport("easyTableNavigator")

    def ActivateCaret (self):
        if self.event_caret==self._on_passThrough:
            self.event_caret = self._on_caret
            inputCore.decide_executeGesture.register(self._on_keyDown)

    def DeactivateCaret (self):
        if self.event_caret!=self._on_passThrough:
            self.event_caret = self._on_passThrough
            inputCore.decide_executeGesture.unregister(self._on_keyDown)

    def ActivateMouseMonitor (self):
        if self.event_mouseMove!=self._on_mouseMove:
            self.event_mouseMove = self._on_mouseMove
            self.timer.Start(200)

    def DeactivateMouseMonitor (self):
        self.timer.Stop()
        if self.autoMouse:
            self.event_mouseMove = self._on_autoMouseMove
        else:
            self.event_mouseMove = self._on_passThrough
        self.startMousePos = (-1, -1)
        self.lastMousePos  = (-1, -1)
        self.lastTime      = 0.0

    def Toggle (self, e=None):
        """
        Used primarily to enable immediate activation/deactivation of positional tones from settings panel.
        """
        if self.active:
            self.Deactivate()
            self.active = False
            if isinstance(e, wx.Event):
                e.Skip()
            return
        self.Activate()
        self.active = True
        if not isinstance(e, wx.Event):
            return
        # Play coordinates of the checkbox to indicate activation
        # And an outline, if outline is selected to be played
        if self.reportOutline:
            self.lastForeground = getForegroundObject()
            wx.CallLater(self.duration+250, self.processForeground)
        try:
            x, y = self._getObjectPos(caret=self.caret)
            playCoordinates(x, y, self.duration, self.lVolume, self.rVolume, self.stereoSwap)
        except:
            pass
        e.Skip()

    def ChangeVolume (self, e):
        """
        Used primarily to change volume immediately from settings panel.
        """
        self.settings.refresh_instance(self, "lVolume", "rVolume")
        e.Skip()
        # Play coordinates of the slider to hear the volume change immediately
        if not self.active:
            return
        try:
            x, y = self._getObjectPos(caret=False)
            playCoordinates(x, y, self.duration, self.lVolume, self.rVolume, self.stereoSwap)
        except:
            pass

    def SwapChannels (self, e):
        """
        Used primarily to swap channels immediately from settings panel.
        """
        self.stereoSwap = e.IsChecked()
        e.Skip()
        # Play coordinates of the checkbox to hear the change immediately
        if not self.active:
            return
        try:
            x, y = self._getObjectPos(caret=False)
            playCoordinates(x, y, self.duration, self.lVolume, self.rVolume, self.stereoSwap)
        except:
            pass

    def ToggleMIDI (self, e):
        if not isinstance(e, wx.Event):
            if self.midi:
                posTones.setGenerator("NVDA")
                self.midi = False
                self.settings["instrument"].enable = False
                return
            try:
                posTones.setGenerator("MIDI")
                self.settings["instrument"].set()
                posTones.player.set_instrument(self.instrument)
                self.midi = True
                self.settings["instrument"].enable = True
            except:
                posTones.setGenerator("NVDA")
                self.midi = False
            return
        if not e.IsChecked():
            e.Skip()
            if not self.midi:
                return
            posTones.setGenerator("NVDA")
            self.midi = False
            self.settings["instrument"].enable = False
            if not self.active:
                return
            try:
                x, y = self._getObjectPos(caret=False)
                playCoordinates(x, y, self.duration, self.lVolume, self.rVolume, self.stereoSwap)
            except:
                pass
            return
        resp = gui.messageBox(DLG_WARN_EXPERIMENTAL, DLG_WARN, wx.ICON_WARNING | wx.YES_NO)
        if resp!=wx.YES:
            e.GetEventObject().SetValue(False)
            return
        e.Skip()
        try:
            posTones.setGenerator("MIDI")
            posTones.player.set_instrument(self.instrument)
            self.midi = True
            self.settings["instrument"].enable = True
            if not self.active:
                return
            try:
                x, y = self._getObjectPos(caret=False)
                playCoordinates(x, y, self.duration, self.lVolume, self.rVolume, self.stereoSwap)
            except:
                pass
        except Exception as err:
            posTones.setGenerator("NVDA")
            self.midi = False
            e.GetEventObject().SetValue(False)
            log.error("Toggling MIDI colossally failed because of "+str(err))

    def ChangeInstrument (self, e):
        if isinstance(e, wx.Event):
            self.instrument = e.GetSelection()
            e.Skip()
        else:
            e.set()
        if self.midi:
            posTones.player.set_instrument(self.instrument)

    def ToggleCaret (self, e=None):
        """
        Used primarily to enable immediate activation/deactivation of positional tones for caret location from settings panel.
        """
        if isinstance(e, wx.Event):
            self.caret = not e.IsChecked() # Just in case of possible mismatch
            e.Skip()
        if self.caret:
            self.DeactivateCaret()
            self.caret = False
            return
        self.ActivateCaret()
        self.caret = True

    def ToggleMouseMonitorAutostart (self, e):
        if isinstance(e, wx.Event):
            self.autoMouse = e.IsChecked()
            e.Skip()
        else:
            e.set()
        self.DeactivateMouseMonitor()

    def ToggleETN (self, e=None):
        if isinstance(e, wx.Event):
            switch = e.IsChecked()
            e.Skip()
        else:
            switch = not self.easyTableNav
        if not self.active:
            # ETN will then be activated or not when user activates objloc, according to the easyTableNav attribute
            self.easyTableNav = switch
            return
        if switch:
            self.easyTableNav = deps.enableAddonSupport("easyTableNavigator", onNavigation=self._on_easyTableNav)            
        else:
            self.easyTableNav = not deps.disableAddonSupport("easyTableNavigator")

    def ToggleForegroundOutline (self, e=None):
        if isinstance(e, wx.Event):
            switch = e.IsChecked()
            if switch and self.active:
                self.lastForeground = None
                wx.CallAfter(self.processForeground)
            e.Skip()
        else:
            switch = not self.reportOutline
        self.reportOutline = switch
        if not self.active:
            return
        if switch:
            self.event_foreground = self._on_foreground
        else:
            self.event_foreground = self._on_passThrough
