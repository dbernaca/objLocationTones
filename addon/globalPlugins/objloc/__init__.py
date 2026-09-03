# Object Location Tones
# A global plugin for NVDA
# Copyright 2017-2024 Joseph Lee, released under GPL
# Copyright 2024-2026 Dalen Bernaca, released under GPL

# Brings NVDA Core issue 2559 to life and more besides

import globalPluginHandler
import inputCore

import speech
import ui
import gui
import wx

from logHandler      import log
from .posTones       import *
from .utils          import *
from .geometry       import *
from .UIStrings      import *
from .settings       import *
from .constants      import *
from ._events        import *
from ._scripts       import *
from .               import posTones
from .               import dependencies as deps

class GlobalPlugin (_objlocEventMethods, _objlocScriptMethods, globalPluginHandler.GlobalPlugin):
    def __init__ (self):
        super(globalPluginHandler.GlobalPlugin, self).__init__()

        # Configurable attributes
        # Note: Settings() later manages auto save and additional args makes them show in settings panel and react to events there

        # Filter function for ints and floats:
        valset = lambda attr, value: attr.original if value<=0 else value

        # Navigation:
        self.active        = Settable(True, # Is real time reporting on or off
                             label=SET_POSITIONAL_AUDIO, group=SET_GROUP_NAVIGATION,
                             reactor=self.Toggle, retractor=self.Toggle)
        self.reportOutline = Settable(False, # Automatically report outline of each activated foreground object
                             label=SET_FOREGROUND_OUTLINE, group=SET_GROUP_NAVIGATION,
                             reactor=self.ToggleForegroundOutline, retractor=self.ToggleForegroundOutline)
        self.easyTableNav  = ETN = Settable(True, # Is cell reporting in ETN layered mode enabled or not
                             label=SET_EASY_TABLE_NAV, group=SET_GROUP_NAVIGATION,
                             reactor=self.ToggleETN, retractor=self.ToggleETN)
        self.duration      = Settable(40, # Duration of a positional tone in Msec
                             label=SET_TONE_DURATION, group=SET_GROUP_NAVIGATION,
                             filter=valset)
        self.locationMode  = Settable(SET_LOCATION_MODE_CHOICES.index(SET_LOCATION_NAVIGATOR_CENTROID), # Which point to use in location presentation of which object
                             choices=tuple(SET_LOCATION_MODE_CHOICES), # tuple() means wx.Choice(), instead of wx.ListBox() in settings panel
                             label=SET_LOCATION_MODE, group=SET_GROUP_NAVIGATION,
                             reactor=lambda e: ( setattr(self, "locationMode", e.GetSelection()), e.Skip() ) )
        # Caret:
        self.caret         = Settable(True,  # Whether to report caret location in editable fields or not
                             label=SET_CARET, group=SET_GROUP_CARET,
                             reactor=self.ToggleCaret, retractor=self.ToggleCaret)
        self.caretMode     = Settable(SET_CARET_CHOICES.index(SET_CARET_BOTH), # Whether to report vertical, horizontal, both or none of caret movements
                             choices=tuple(SET_CARET_CHOICES), # tuple() means wx.Choice(), instead of wx.ListBox() in settings panel
                             label=SET_CARET_REPORT, group=SET_GROUP_CARET,
                             reactor=lambda e: ( setattr(self, "caretMode", e.GetSelection()), e.Skip() ) )
        self.caretTyping   = Settable(False, # Whether to report caret location while typing or not
                             label=SET_CARET_TYPING, group=SET_GROUP_CARET,
                             reactor=lambda e: (setattr(self, "caretTyping", e.IsChecked()), e.Skip()) )
        self.durationCaret = Settable(40, # Duration of a positional tone for caret reporting in Msec
                             label=SET_TONE_DURATION_CARET, group=SET_GROUP_CARET,
                             filter=valset)
        # Mouse:
        self.tolerance     = Settable(20, # Mouse to location arrivall detection tolerance,
                                          # refers to distance between two points in pixels
                             label=SET_MOUSE_TOLERANCE, group=SET_GROUP_MOUSE,
                             filter=valset)
        self.timeout       = Settable(2.0, # Timeout after which to stop the mouse monitoring automatically (in seconds)
                             label=SET_MOUSE_MONITOR_TIMEOUT, group=SET_GROUP_MOUSE,
                             filter=valset)
        self.autoMouse     = Settable(False,
                             label=SET_MOUSE_MONITOR_AUTO_START, group=SET_GROUP_MOUSE,
                             reactor=self.ToggleMouseMonitorAutostart, retractor=self.ToggleMouseMonitorAutostart)
        self.refPoint      = Settable(SET_MOUSE_REF_CHOICES.index(SET_MOUSE_REF_FOCUS), # Which point location to announce along with the current mouse position
                             choices=tuple(SET_MOUSE_REF_CHOICES), # tuple() means wx.Choice(), instead of wx.ListBox() in settings panel
                             label=SET_MOUSE_REF_POINT, group=SET_GROUP_MOUSE,
                             reactor=lambda e: ( setattr(self, "refPoint", e.GetSelection()), e.Skip() ) )
        self.stopMessage   = Settable(True,
                             label=SET_MOUSE_MONITOR_STOP_MESSAGE, group=SET_GROUP_MOUSE,
                             reactor=lambda e: ( setattr(self, "stopMessage", e.IsChecked()), e.Skip() ) )
        # Tones:
        # * Temporary controls for MIDI until out of experimental phase
        self.midi          = Settable(False,
                             label=SET_MIDI, group=SET_GROUP_TONES,
                             reactor=self.ToggleMIDI, retractor=self.ToggleMIDI)
        self.instrument    = Settable(115,
                             choices=tuple(posTones.general_midi_instruments),
                             label=SET_MIDI_INSTRUMENT, group=SET_GROUP_TONES, enabled=False,
                             reactor=self.ChangeInstrument, retractor=self.ChangeInstrument)
        #self.midiSynth     = Settable(0,
        #                     choices=tuple(),
        #                     label=SET_MIDI_SYNTHESIZER, group=SET_GROUP_TONES,
        #                     finisher=lambda attr: attr.get_gui_control().Set([x[1] for x in posTones.midi.list_output_devices()]))
        self.lVolume       = Settable(maxVolume, # Volume of positional tones on the left stereo channel, float in range 0.0 to 1.0
                             label=SET_LEFT_VOLUME, group=SET_GROUP_TONES,
                             min=1, max=100, ratio=100,
                             reactor=self.ChangeVolume)
        self.rVolume       = Settable(maxVolume, # Volume of positional tones on the right stereo channel, float in range 0.0 to 1.0
                             label=SET_RIGHT_VOLUME, group=SET_GROUP_TONES,
                             min=1, max=100, ratio=100,
                             reactor=self.ChangeVolume)
        self.stereoSwap    = Settable(False, # Swap stereo sides
                             label=SET_SWAP_STEREO_CHANNELS, group=SET_GROUP_TONES,
                             reactor=self.SwapChannels)
        # Make particular dependency related options not show in settings dialog if that add-on is not available
        ETN.show = deps.checkAddonUsability("easyTableNavigator",
                   logging=False,
                   filter=(lambda addon: addon.version>="2.8"))
        # Load the configurables from settings if possible
        self.settings = S = Settings()
        try:
            S.load(self)
        except SettingsError as e:
            log.warning(str(e))
        if ETN.value and not ETN.show:
            # If settings says to use, but ETN became unavailable, just disable it internally for this session
            self.easyTableNav = False
            ETN.value = False
            ETN.save = False # Do not save the value change in this case, so if ETN returns the setting is valid once more
        # Setup a settings panel
        SetPanel(S, self)

        # Flow control flags
        self.focusing     = True  # A flag to prevent double tones on focus of text area children
                                  # right after a parent window is brought to top
                                  # might not be needed in the future
        self.typing       = False # A flag to prevent tones during typing
        self.entered      = False # A flag for reporting entering and exiting of the focused object area
        self.processing   = False # A flag to avoid collisions of positional audio upon fast subsequent keypresses

        # Temporary variables for action checks
        self.startMousePos  = (-1, -1) # Used to mark a point from which mouse started
        self.lastMousePos   = (-1, -1) # Used to detect that the mouse stopped moving so that we can stop the timer
        self.lastTime       = 0.0 # Used to detect how much time passed after mouse stopped moving
        self.lastKey        = None # What was the last key pressed (InputKeyboardGesture() object)
        self.lastForeground = None # What was the last foreground object

        # Bind functions as attributes for speedy access and live switching
        if IS_LOCATION_MODE_CENTROID(self.locationMode):
            self._getObjectPos = getObjectPosCenter
        elif IS_LOCATION_MODE_LEFT(self.locationMode):
            self._getObjectPos = getObjectPosLeft
        else:
            self._getObjectPos = getObjectPosRight

        if IS_LOCATION_MODE_NAVIGATOR(self.locationMode):
            self._getObject = getNavigatorObject
        else:
            self._getObject = getFocusObject

        if self.refPoint==MOUSE_REF_NAVIGATOR:
            self._getRefObject = getNavigatorObject
        else:
            self._getRefObject = getFocusObject

        # Mouse monitoring position playing timer
        self.timer = wx.Timer(gui.mainFrame)
        gui.mainFrame.Bind(wx.EVT_TIMER, self._on_mouseMonitor, self.timer)

        # Initial NVDA event bindings
        if self.active:
            self.Activate()
        else:
            self.event_becomeNavigatorObject = self._on_passThrough
            self.event_gainFocus = self._on_passThrough
            self.event_foreground = self._on_passThrough
            if self.caret:
                self.ActivateCaret()
            else:
                self.event_caret = self._on_passThrough
        if self.autoMouse:
            self.event_mouseMove = self._on_autoMouseMove
        else:
            self.event_mouseMove = self._on_passThrough
        if self.midi:
            try:
                posTones.setGenerator("MIDI")
                posTones.player.set_instrument(self.instrument)
                self.settings["instrument"].enable = True
            except:
                posTones.setGenerator("NVDA")
                self.midi = False

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

    def terminate (self):
        """
        Removes any unnecessary, and potentially dangerous when objloc is not running, events from NVDA.
        Also, saves all current settings.
        This ensures smooth ending and reloading of the objloc add-on.
        """
        self.timer.Stop()
        gui.mainFrame.Unbind(wx.EVT_TIMER, handler=self._on_mouseMonitor, source=self.timer)
        inputCore.decide_executeGesture.unregister(self._on_keyDown)
        try:
            posTones.setGenerator("NVDA")
        except:
            pass
        try:
            self.settings.save(self)
        except SettingsError as e:
            log.warning(str(e))
        if self.easyTableNav:
            deps.disableAddonSupport("easyTableNavigator")
        del self.settings
        RemovePanel()
