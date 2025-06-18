# Object Location Tones
# A global plugin for NVDA
# Copyright 2017-2024 Joseph Lee, released under GPL
# Copyright 2024-2025 Dalen Bernaca, released under GPL

# Brings NVDA Core issue 2559 to life and more besides

import globalPluginHandler
import inputCore

import speech
import ui
import gui
import wx

from scriptHandler   import script, getLastScriptRepeatCount
from keyboardHandler import KeyboardInputGesture
from logHandler      import log
from .posTones     import *
from .utils        import *
from .geometry     import *
from .UIStrings    import *
from .settings     import *
from .             import posTones
from time import monotonic as time

class GlobalPlugin (globalPluginHandler.GlobalPlugin):
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
        self.duration      = Settable(40, # Duration of a positional tone in Msec
                             label=SET_TONE_DURATION, group=SET_GROUP_NAVIGATION,
                             filter=valset)
        # Caret:
        self.caret         = Settable(True, label=SET_CARET, group=SET_GROUP_CARET, # Whether to report caret location in editable fields or not
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
        self.refPoint      = Settable(SET_MOUSE_REF_CHOICES.index(SET_MOUSE_REF_FOCUS), # Whether to report vertical, horizontal, both or none of caret movements
                             choices=tuple(SET_MOUSE_REF_CHOICES), # tuple() means wx.Choice(), instead of wx.ListBox() in settings panel
                             label=SET_MOUSE_REF_POINT, group=SET_GROUP_MOUSE,
                             reactor=lambda e: ( setattr(self, "refPoint", e.GetSelection()), e.Skip() ) )
        # Tones:
        # * Temporary controls for MIDI until out of experimental phase
        self.midi          = Settable(False,
                             label=SET_MIDI, group=SET_GROUP_TONES,
                             reactor=self.ToggleMIDI, retractor=self.ToggleMIDI)
        self.instrument    = Settable(115,
                             choices=tuple(posTones.general_midi_instruments),
                             label=SET_MIDI_INSTRUMENT, group=SET_GROUP_TONES,
                             reactor=self.ChangeInstrument, retractor=self.ChangeInstrument)
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

        # Load the configurables from settings if possible
        self.settings = S = Settings()
        try:
            S.load(self)
        except SettingsError as e:
            log.warning(str(e))
        # Setup a settings panel
        SetPanel(S, self)

        # Flow control flags
        self.focusing     = True  # A flag to prevent double beeps on focus of text area children
                                  # right after a parent window is brought to top
                                  # might not be needed in the future
        self.typing       = False # A flag to prevent beeps during typing
        self.entered      = False # A flag for reporting entering and exiting of the focused object area
        self.processing   = False # A flag to avoid collisions of positional audio upon fast subsequent keypresses

        # Temporary variables for action checks
        self.lastMousePos = (-1, -1) # Used to detect that the mouse stopped moving so that we can stop the timer
        self.lastTime     = 0.0 # Used to detect how much time passed after mouse stopped moving
        self.lastKey      = None # What was the last key pressed (InputKeyboardGesture() object)

        # Mouse monitoring position playing timer
        self.timer = wx.Timer(gui.mainFrame)
        gui.mainFrame.Bind(wx.EVT_TIMER, self._on_mouseMonitor, self.timer)

        # Initial NVDA event bindings
        if self.active:
            self.Activate()
        else:
            self.event_becomeNavigatorObject = self._on_passThrough
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
            except:
                posTones.setGenerator("NVDA")
                self.midi = False

    def Activate (self):
        self.event_becomeNavigatorObject = self._on_becomeNavigatorObject
        if self.caret:
            self.ActivateCaret()
        self.focusing = True
        self.typing = False

    def Deactivate (self):
        self.event_becomeNavigatorObject = self._on_passThrough
        self.DeactivateCaret()

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
        self.lastMousePos = (-1, -1)
        self.lastTime = 0.0

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
        try:
            x, y = getObjectPos(caret=self.caret)
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
            x, y = getObjectPos(caret=self.caret)
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
            x, y = getObjectPos(caret=self.caret)
            playCoordinates(x, y, self.duration, self.lVolume, self.rVolume, self.stereoSwap)
        except:
            pass

    def ToggleMIDI (self, e):
        if not isinstance(e, wx.Event):
            if self.midi:
                posTones.setGenerator("NVDA")
                self.midi = False
                return
            try:
                posTones.setGenerator("MIDI")
                self.settings["instrument"].set()
                posTones.player.set_instrument(self.instrument)
                self.midi = True
            except:
                posTones.setGenerator("NVDA")
                self.midi = False
            return
        if not e.IsChecked():
            if not self.midi:
                return e.Skip()
            posTones.setGenerator("NVDA")
            self.midi = False
            try:
                x, y = getObjectPos(caret=self.caret)
                playCoordinates(x, y, self.duration, self.lVolume, self.rVolume, self.stereoSwap)
            except:
                pass
            return e.Skip()
        resp = gui.messageBox(DLG_WARN_EXPERIMENTAL, DLG_WARN, wx.ICON_WARNING | wx.YES_NO)
        if resp!=wx.YES:
            e.GetEventObject().SetValue(False)
            return
        try:
            posTones.setGenerator("MIDI")
            posTones.player.set_instrument(self.instrument)
            self.midi = True
            try:
                x, y = getObjectPos(caret=self.caret)
                playCoordinates(x, y, self.duration, self.lVolume, self.rVolume, self.stereoSwap)
            except:
                pass
        except Exception as e:
            posTones.setGenerator("NVDA")
            self.midi = False
            e.GetEventObject().SetValue(False)
            log.error("Toggling MIDI colossally failed because of "+str(e))
        e.Skip()

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
        del self.settings
        RemovePanel()

    @script(
        gesture="kb:control+Shift+NumpadDelete",
        description=IG_OUTLINE, category=IG_CATEGORY)
    def script_objectOutline (self, gesture):
        """
        Plays positional tones for all 4 corners of the object's bounding box.
        If the object is editable, adds a final tone for the caret position.
        """
        if self.processing or getLastScriptRepeatCount():
            return
        try:
            obj = getFocusObject()
            rect = BBox(obj)
            after = playPoints(200, rect.corners, self.duration+20, self.lVolume, self.rVolume, self.stereoSwap)
            ui.message(getObjectDescription(obj))
            if self.caret:
                try:
                    oX, oY = getCaretPos(obj)
                    wx.CallLater(after+40, playCoordinates, oX, oY, self.durationCaret+150, self.lVolume, self.rVolume, self.stereoSwap)
                except:
                    pass
        except:
            ui.message(MSG_LOCATION_UNAVAILABLE)

    @script(
        gesture="kb:control+Shift+alt+NumpadDelete",
        description=IG_PARENT_OUTLINE, category=IG_CATEGORY)
    def script_parentObjectOutline (self, gesture):
        """
        Plays positional tones for all 4 corners of the object parent's bounding box.
        """
        if self.processing:
            # Do not allow repeat before the last outline is played in full
            # nor adding more requests for the processing using CallLater()
            return
        self.processing = True
        # Delay before playing for a bit so that we can detect repeated gesture later
        # and choose the requested ancestor accordingly
        # Note that the script will be called multiple times if the gesture is repeated
        # and the repeat counter will be increased,
        # but only one processing will take place, after the delay timeout
        # This is simple and stupid and a much better algorithm is planned for the future
        # This one guarantees frustration if user cannot use the gesture fast enough
        # and a long delay, as this one must be, after a requested action is not conducive in user interfaces anyway
        wx.CallLater(500, self.processParentObjectOutline, gesture)

    def processParentObjectOutline (self, gesture):
        """
        This method actually plays the positional outline for an ancestor object
        after being called after a delay needed to detect how deep
        in the ancestors tree the user wants to go.
        """
        count = getLastScriptRepeatCount()
        try:
            obj = getFocusObject()
            level = 0
            for _ in range(count+1):
                if not obj.parent or obj==obj.parent:
                    break
                obj = obj.parent
                level += 1
            if level==0:
                ui.message(MSG_PARENT_NOT_AVAILABLE)
                return
            rect = BBox(obj)
            after = playPoints(200, rect.corners, self.duration+20, self.lVolume, self.rVolume, self.stereoSwap)
            wx.CallLater(after+self.duration+20, setattr, self, "processing", False)
            ui.message(MSG_ANCESTOR % (getObjectDescription(obj), level))
        except:
            ui.message(MSG_LOCATION_UNAVAILABLE)
            self.processing = False

    @script(
        gesture="kb:Shift+NumpadDelete",
        description=IG_TOGGLE_MOUSE_MONITOR, category=IG_CATEGORY)
    def script_toggleMouseMonitor (self, gesture):
        """
        Activates or deactivates real-time mouse location monitoring.
        The location is presented in relation to the focused object's centroid
        or the caret position within an editable field.
        """
        if not self.timer.IsRunning():
            try:
                fobj = getFocusObject()
                oX, oY = getObjectPos(fobj, caret=self.caret)
                mX, mY = getCursorPos()
            except:
                ui.message(MSG_LOCATION_UNAVAILABLE)
                return
            dist = abs(oX-mX) + abs(oY-mY)
            if dist<=self.tolerance:
                playCoordinates(oX, oY, self.duration+150, self.lVolume, self.rVolume, self.stereoSwap)
                ui.message(MSG_MOUSE_ALREADY_THERE)
                return
            self.entered = (mX, mY) in BBox(fobj)
            self.ActivateMouseMonitor()
            return
        self.DeactivateMouseMonitor()
        speech.cancelSpeech()
        ui.message(MSG_MOUSE_MONITOR_CANCELLED)

    @script(
        gesture="kb:Windows+NumpadDelete",
        description=IG_MOUSE_POSITION, category=IG_CATEGORY)
    def script_mouse (self, gesture):
        """
        Plays positional tone for a mouse cursor location on demand.
        """
        self.DeactivateMouseMonitor()
        try:
            x, y = getCursorPos()
            playCoordinates(x, y, self.duration+50, self.lVolume, self.rVolume, self.stereoSwap)
        except:
            pass

    @script(
        gesture="kb:NumpadDelete",
        description=IG_OBJECT_LOCATION, category=IG_CATEGORY)
    def script_locate (self, gesture):
        """
        Plays positional tone for currently focused object location on demand
        """
        self.DeactivateMouseMonitor()
        try:
            x, y = getObjectPos(caret=self.caret)
            playCoordinates(x, y, self.duration+30, self.lVolume, self.rVolume, self.stereoSwap)
        except:
            pass

    @script(
        gesture="kb:Control+NumpadDelete",
        description=IG_TOGGLE_LOCATION_REPORTING, category=IG_CATEGORY)
    def script_toggle (self, gesture):
        """
        Toggles positional tones on or off by swapping
        relevant event handlers accordingly.
        """
        self.DeactivateMouseMonitor()
        self.Toggle()
        self.settings.refresh_panel(self, "active")
        ui.message(MSG_POSITIONAL_TONES_ON if self.active else MSG_POSITIONAL_TONES_OFF)

    @script(
        gesture="kb:control+windows+NumpadDelete",
        description=IG_TOGGLE_CARET_LOCATION_REPORTING, category=IG_CATEGORY)
    def script_toggleCaret (self, gesture):
        """
        Toggles positional tones for caret location on or off by swapping
        relevant event handlers accordingly.
        """
        self.DeactivateMouseMonitor()
        if self.caret and not self.active:
            if self.event_caret==self._on_passThrough:
                # Deactivated by global toggle with script_toggle():
                self.ActivateCaret()
                msg = MSG_CARET_TONES_ON
            else:
                self.DeactivateCaret()
                self.caret = False
                msg = MSG_CARET_TONES_OFF
        else:
            self.ToggleCaret()
            msg = MSG_CARET_TONES_ON if self.caret else MSG_CARET_TONES_OFF
        self.settings.refresh_panel(self, "caret")
        ui.message(msg)

    @script(
        gesture="kb:control+alt+windows+NumpadDelete",
        description=IG_CYCLE_CARET_MODE, category=IG_CATEGORY)
    def script_cycleCaretMode (self, gesture):
        """
        Cycles through available caret reporting modes.
        """
        self.DeactivateMouseMonitor()
        mode = self.caretMode+1
        mode = 0 if mode==len(SET_CARET_CHOICES) else mode
        self.caretMode = mode
        self.settings.refresh_panel(self, "caretMode")
        ui.message(SET_CARET_REPORT+" "+SET_CARET_CHOICES[mode])

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
            x, y = getObjectPos(obj, caret=self.caret)
            playCoordinates(x, y, self.duration, self.lVolume, self.rVolume, self.stereoSwap)
        except:
            pass
        nextHandler()

    event_becomeNavigatorObject = _on_becomeNavigatorObject

    def _on_caret (self, obj, nextHandler):
        """
        Event handler that plays a positional tone upon caret movements.
        """
        if self.focusing:
            # Skip a caret beep right after text area gained focus because becomeNavigator fires first
            self.focusing = False
            return nextHandler()
        if self.typing:
            # Caret moved because user is typing or editing the text:
            if not self.caretTyping:
                return nextHandler()
            try:
                x, y = getCaretPos(obj)
                playCoordinates(x, y, self.durationCaret, self.lVolume, self.rVolume, self.stereoSwap)
            except:
                pass
            return nextHandler()
        if self.caretMode==3:
            # Do not report movements is selected
            return nextHandler()
        # Caret navigation:
        name = getKeyName(self.lastKey)
        if self.caretMode==0 and name not in ("upArrow", "downArrow", "pageUp", "pageDown", "enter", "control+home", "control+end"):
            # Vertical navigation
            pass
        elif self.caretMode==1 and name not in ("leftArrow", "rightArrow", "home", "end"):
            # Horizontal navigation
            pass
        else:
            try:
                x, y = getCaretPos(obj)
                playCoordinates(x, y, self.durationCaret, self.lVolume, self.rVolume, self.stereoSwap)
            except:
                pass
        nextHandler()

    event_caret = _on_passThrough

    def _on_mouseMonitor (self, e):
        """
        Timer callback to play positional tones of a mouse cursor location and the current reference point.
        Helps to monitor their relation, i.e. difference of their distance on the screen.
        """
        try:
            mp     = getCursorPos()
            oX, oY = getObjectPos(caret=self.caret)
        except:
            self.DeactivateMouseMonitor()
            ui.message(MSG_LOCATION_UNAVAILABLE)
            return
        # If mouse is stationary for too long, automatically stop monitoring:
        t   = time()
        lmp = self.lastMousePos
        if lmp==mp and t-self.lastTime>=self.timeout:
            self.DeactivateMouseMonitor()
            ui.message(MSG_MOUSE_MONITOR_STOPPED)
            return
        if lmp!=mp:
            self.lastMousePos = mp
            self.lastTime = t
        wx.CallAfter(playCoordinates, mp[0], mp[1], self.duration+40, self.lVolume, self.rVolume, self.stereoSwap)
        if self.refPoint==0:
            # Play focused objects pos as a ref point
            wx.CallLater(self.duration+100, playCoordinates, oX, oY, self.duration+70, self.lVolume, self.rVolume, self.stereoSwap)
        elif self.refPoint==1:
            # Top left of the foreground window
            try:
                wlpx, wlpy, _, _ = getForegroundObject().location
            except:
                return
            wx.CallLater(self.duration+100, playCoordinates, wlpx, wlpy, self.duration+70, self.lVolume, self.rVolume, self.stereoSwap)
        elif self.refPoint==2:
            # Center of the foreground window
            try:
                wcpx, wcpy = getForegroundObject().location.center
            except:
                return
            wx.CallLater(self.duration+100, playCoordinates, wcpx, wcpy, self.duration+70, self.lVolume, self.rVolume, self.stereoSwap)
        elif self.refPoint==3:
            # Top left corner of the screen, that is (0, 0)
            wx.CallLater(self.duration+100, playCoordinates, 0, 0, self.duration+70, self.lVolume, self.rVolume, self.stereoSwap)
        elif self.refPoint==4:
            # Center of the virtual screen as given by the desktop object
            try:
                dcpx, dcpy = getDesktopObject().location.center
            except:
                return
            wx.CallLater(self.duration+100, playCoordinates, dcpx, dcpy, self.duration+70, self.lVolume, self.rVolume, self.stereoSwap)
        #else:
        #    # None --> Play the same coordinates twice in a row
        #    wx.CallLater(self.duration+100, playCoordinates, mp[0], mp[1], self.duration+70, self.lVolume, self.rVolume, self.stereoSwap)

    def _on_mouseMove (self, obj, nextHandler, x, y):
        """
        NVDA event used during mouse monitoring that checks for the current
        location of mouse cursor in relation to focused object or caret position.
        If cursor is in tolerated distance, the hit is reported and monitoring ends.
        The event also reports entering and exiting the focused object.
        """
        try:
            fobj = getFocusObject()
            oX, oY = getObjectPos(fobj, caret=self.caret)
        except:
            self.DeactivateMouseMonitor()
            ui.message(MSG_LOCATION_UNAVAILABLE)
            nextHandler()
            return
        if (x, y) in BBox(fobj):
            if not self.entered:
                self.entered = True
                speech.cancelSpeech()
                ui.message(MSG_ENTERING+" "+getObjectDescription(fobj))
        else:
            if self.entered:
                speech.cancelSpeech()
                ui.message(MSG_EXITING+" "+getObjectRoleName(fobj))
            self.entered = False
        dist = abs(oX-x) + abs(oY-y)
        if dist<=self.tolerance:
            playCoordinates(oX, oY, self.duration+150, self.lVolume, self.rVolume, self.stereoSwap)
            self.DeactivateMouseMonitor()
            speech.cancelSpeech()
            ui.message(MSG_LOCATION_REACHED)
        nextHandler()

    def _on_autoMouseMove (self, obj, nextHandler, x, y):
        """
        NVDA event used to auto-start mouse monitoring after a mouse moves.
        """
        try:
            self.entered = (x, y) in BBox(getFocusObject())
        except:
            pass
        self.ActivateMouseMonitor()
        nextHandler()

    event_mouseMove = _on_passThrough

    def _on_keyDown (self, gesture):
        """
        Notifies other relevant methods that typing has taken  place.
        """
        if isinstance(gesture, KeyboardInputGesture):
            self.lastKey = gesture
            wx.CallAfter(self.typing_handler, gesture)
        return True

    def typing_handler (self, gesture):
        # self.typing is true only when a pressed key is capable of changing a text editable
        # typing will wrongly indicate True in read only fields
        # also, in edit fields that do not process enter and/or tab keys,
        # but since we use it only in event_caret() handler it will not cause problems
        # Automatic caret event upon gaining focus should not report, thus last key from previous field shouldn't cause an erroneous report
        self.typing = willEnterText(gesture)
