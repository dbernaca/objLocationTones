# Object Location Tones
# A global plugin for NVDA
# Copyright 2017-2024 Joseph Lee, released under GPL
# Copyright      2024  Dalen Bernaca, released under GPL

# Brings NVDA Core issue 2559 to life and more besides

import globalPluginHandler
import inputCore

import config
import speech
import ui
import gui
import wx

from scriptHandler import script, getLastScriptRepeatCount
from logHandler    import log
from tones         import beep
from .utils        import *
from .geometry     import *
from .UIStrings    import *
from .settings     import *
try:
    from time import monotonic as time
except:
    from time import time

# Some initial values from NVDA configuration
minPitch  = config.conf['mouse']['audioCoordinates_minPitch']
maxPitch  = config.conf['mouse']['audioCoordinates_maxPitch']
maxVolume = config.conf['mouse']['audioCoordinates_maxVolume']

def valset (attr, value):
    if value<=0:
        return attr.original
    return value

class GlobalPlugin (globalPluginHandler.GlobalPlugin):
    def __init__ (self):
        super(globalPluginHandler.GlobalPlugin, self).__init__()

        # Configurable attributes (in the future)
        self.active     = Settable(True, # Is real time reporting on or off
                          label=SET_POSITIONAL_AUDIO, ordinal=0, callable=self.Toggle)
        self.duration   = Settable(40, # Duration of a positional tone in Msec
                          label=SET_TONE_DURATION, validator=valset, ordinal=1)
        self.lVolume    = Settable(maxVolume, # Volume of positional tones on the left stereo channel, float in range 0.0 to 1.0
                          label=SET_LEFT_VOLUME, min=1, max=100, ratio=100, ordinal=5)
        self.rVolume    = Settable(maxVolume, # Volume of positional tones on the right stereo channel, float in range 0.0 to 1.0
                          label=SET_RIGHT_VOLUME, min=1, max=100, ratio=100, ordinal=6)
        self.stereoSwap = Settable(False, # Swap stereo sides
                          label=SET_SWAP_STEREO_CHANNELS, ordinal=7, callable=self.SwapChannels)
        self.tolerance  = Settable(20, # Mouse to location arrivall detection tolerance,
                                       # refers to distance between two points in pixels
                          label=SET_MOUSE_TOLERANCE, validator=valset, ordinal=2)
        self.timeout    = Settable(2.0, # Timeout after which to stop the mouse monitoring automatically (in seconds)
                          label=SET_MOUSE_MONITOR_TIMEOUT, validator=valset, ordinal=3)
        self.caret      = Settable(True) # Whether to report caret location for editable fields or not
                                         # Not yet included in settings panel
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
        self.lastKey      = None # What was the last key pressed
        self.lastCoords   = (-1, -1, 0.0) # Last coordinates played (for avoiding doubleing tones for any reason)
                                          # values are (x, y, <tone duration>)
        self.lastPlayed   = 0.0 # When the last tone was played (to detect tone doubles requested before their time) (in seconds)

        # Mouse monitoring position playing timer
        self.timer = wx.Timer(gui.mainFrame)
        gui.mainFrame.Bind(wx.EVT_TIMER, self._on_mouseMonitor, self.timer)

        # Initial NVDA event bindings
        if self.active:
            self.event_becomeNavigatorObject = self._on_becomeNavigatorObject
            self.event_caret = self._on_caret
            inputCore.decide_executeGesture.register(self._on_keyDown)
        else:
            self.event_becomeNavigatorObject = self._on_passThrough
            self.event_caret = self._on_passThrough
        self.event_mouseMove = self._on_passThrough

    def Activate (self):
        self.event_becomeNavigatorObject = self._on_becomeNavigatorObject
        self.event_caret = self._on_caret
        inputCore.decide_executeGesture.register(self._on_keyDown)
        self.focusing = True
        self.typing = False

    def Deactivate (self):
        self.event_becomeNavigatorObject = self._on_passThrough
        self.event_caret = self._on_passThrough
        inputCore.decide_executeGesture.unregister(self._on_keyDown)

    def Toggle (self, *args, **kwargs):
        """
        Used primarily to enable immediate activation/deactivation of positional tones from settings panel.
        """
        if self.active:
            self.Deactivate()
            self.active = False
        else:
            self.Activate()
            self.active = True

    def SwapChannels (self, e):
        """
        Used primarily to swap channels immediately from settings panel.
        """
        self.stereoSwap = e.IsChecked()

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
            self.settings.save(self)
        except SettingsError as e:
            log.warning(str(e))
        del self.settings
        RemovePanel()

    def playCoordinates (self, x, y, d=None):
        """
        Plays a positional tone for given x and y coordinates,
        relative to current desktop window size.
        If the method is called more than once with same coordinates and already playing,
        the duplicate call will not produce any tones.
        If the coordinates represent a point that is located out of the screen,
        the tone will also not be played.
        """
        screenWidth, screenHeight = getDesktopObject().location[2:]
        # If the same coordinates were just played, and asked to be played again before the last tone ended
        # just don't do it and that is that.
        t = time()
        lx, ly, ld = self.lastCoords
        if x==lx and ly==ly and t-self.lastPlayed<=ld:
            return
        if 0 <= x <= screenWidth and 0 <= y <= screenHeight:
            curPitch = minPitch + ((maxPitch - minPitch) * ((screenHeight - y) / float(screenHeight)))
            if self.stereoSwap:
                rightVolume = int((85 * ((screenWidth - float(x)) / screenWidth)) * self.rVolume)
                leftVolume = int((85 * (float(x) / screenWidth)) * self.lVolume)
            else: 
                leftVolume = int((85 * ((screenWidth - float(x)) / screenWidth)) * self.lVolume)
                rightVolume = int((85 * (float(x) / screenWidth)) * self.rVolume)
            d = d or self.duration
            beep(curPitch, d, left=leftVolume, right=rightVolume)
            self.lastPlayed = t
            self.lastCoords = (x, y, d/1000.0)

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
            wx.CallAfter(self.playCoordinates, rect.X1, rect.Y1, self.duration+20)
            wx.CallLater(self.duration+220, self.playCoordinates, rect.X2, rect.Y2, self.duration+20)
            wx.CallLater(self.duration+620, self.playCoordinates, rect.X3, rect.Y3, self.duration+20)
            wx.CallLater(self.duration+820, self.playCoordinates, rect.X4, rect.Y4, self.duration+20)
            ui.message(getObjectDescription(obj))
            try:
                oX, oY = getCaretPos(obj)
                wx.CallLater(self.duration+1120, self.playCoordinates, oX, oY, self.duration+150)
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
            wx.CallAfter(self.playCoordinates, rect.X1, rect.Y1, self.duration+20)
            wx.CallLater(self.duration+220, self.playCoordinates, rect.X2, rect.Y2, self.duration+20)
            wx.CallLater(self.duration+620, self.playCoordinates, rect.X3, rect.Y3, self.duration+20)
            wx.CallLater(self.duration+820, self.playCoordinates, rect.X4, rect.Y4, self.duration+20)
            wx.CallLater(self.duration+840+self.duration, setattr, self, "processing", False)
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
                oX, oY = getObjectPos(caret=self.caret)
                mX, mY = getCursorPos()
            except:
                ui.message(MSG_LOCATION_UNAVAILABLE)
                return
            dist = abs(oX-mX) + abs(oY-mY)
            if dist<=self.tolerance:
                self.playCoordinates(oX, oY, self.duration+150)
                ui.message(MSG_MOUSE_ALREADY_THERE)
                return
            self.event_mouseMove = self._on_mouseMove
            self.timer.Start(200)
            return
        self.timer.Stop()
        self.lastMousePos = (-1, -1)
        self.lastTime = 0.0
        self.event_mouseMove = self._on_passThrough
        speech.cancelSpeech()
        ui.message(MSG_MOUSE_MONITOR_CANCELLED)

    @script(
        gesture="kb:Windows+NumpadDelete",
        description=IG_MOUSE_POSITION, category=IG_CATEGORY)
    def script_mouse (self, gesture):
        """
        Plays positional tone for a mouse cursor location on demand.
        """
        self.timer.Stop()
        self.event_mouseMove = self._on_passThrough
        self.lastMousePos = (-1, -1)
        self.lastTime = 0.0
        try:
            x, y = getCursorPos()
            self.playCoordinates(x, y, self.duration+50)
        except:
            pass

    @script(
        gesture="kb:NumpadDelete",
        description=IG_OBJECT_LOCATION, category=IG_CATEGORY)
    def script_locate (self, gesture):
        """
        Plays positional tone for currently focused object location on demand
        """
        self.timer.Stop()
        self.event_mouseMove = self._on_passThrough
        self.lastMousePos = (-1, -1)
        self.lastTime = 0.0
        try:
            x, y = getObjectPos(caret=self.caret)
            self.playCoordinates(x, y, self.duration+30)
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
        if not self.active:
            self.Activate()
            ui.message(MSG_POSITIONAL_TONES_ON)
            self.active = True
            return
        self.Deactivate()
        self.timer.Stop()
        self.event_mouseMove = self._on_passThrough
        self.lastMousePos = (-1, -1)
        self.lastTime = 0.0
        ui.message(MSG_POSITIONAL_TONES_OFF)
        self.active = False

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
            self.playCoordinates(x, y)
        except:
            pass
        nextHandler()

    event_becomeNavigatorObject = _on_becomeNavigatorObject

    def _on_caret (self, obj, nextHandler):
        """
        Event handler that plays a positional tone upon caret movements.
        """
        if self.focusing or self.typing:
            # Skip a caret beep right after text area gained focus because becomeNavigator fires first
            # or if user is typing in the text
            self.focusing = False
            nextHandler()
            return
        try:
            x, y = getCaretPos(obj)
            self.playCoordinates(x, y)
        except:
            pass
        nextHandler()

    event_caret = _on_caret

    def _on_mouseMonitor (self, e):
        """
        Timer callback to play positional tones of a mouse cursor location and the current navigator object.
        Helps to monitor their relation, i.e. difference of their distance on the screen.
        """
        try:
            mp     = getCursorPos()
            oX, oY = getObjectPos(caret=self.caret)
        except:
            self.timer.Stop()
            self.lastMousePos = (-1, -1)
            self.lastTime     = 0.0
            self.event_mouseMove = self._on_passThrough
            ui.message(MSG_LOCATION_UNAVAILABLE)
            return
        # If mouse is stationary for too long, automatically stop monitoring:
        t   = time()
        lmp = self.lastMousePos
        if lmp==mp and t-self.lastTime>=self.timeout:
            self.lastMousePos = (-1, -1)
            self.lastTime     = 0.0
            self.timer.Stop()
            self.event_mouseMove = self._on_passThrough
            ui.message(MSG_MOUSE_MONITOR_STOPPED)
            return
        if lmp!=mp:
            self.lastMousePos = mp
            self.lastTime = t
        wx.CallAfter(self.playCoordinates, mp[0], mp[1], self.duration+40)
        wx.CallLater(self.duration+100, self.playCoordinates, oX, oY, self.duration+70)

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
            self.timer.Stop()
            self.lastMousePos = (-1, -1)
            self.lastTime     = 0.0
            self.event_mouseMove = self._on_passThrough
            ui.message(MSG_LOCATION_UNAVAILABLE)
            nextHandler()
            return
        if (x, y) in BBox(fobj):
            if not self.entered:
                self.entered = True
                speech.cancelSpeech()
                ui.message(MSG_ENTERING)
        else:
            if self.entered:
                speech.cancelSpeech()
                ui.message(MSG_EXITING)
            self.entered = False
        dist = abs(oX-x) + abs(oY-y)
        if dist<=self.tolerance:
            self.playCoordinates(oX, oY, self.duration+150)
            self.timer.Stop()
            self.event_mouseMove = self._on_passThrough
            self.lastMousePos = (-1, -1)
            self.lastTime     = 0.0
            speech.cancelSpeech()
            ui.message(MSG_LOCATION_REACHED)
        nextHandler()

    event_mouseMove = _on_passThrough

    def _on_keyDown (self, gesture):
        """
        Notifies other relevant methods that typing has taken  place.
        """
        try:
            name = gesture.mainKeyName
        except AttributeError:
            return True
        self.lastKey = name
        if len(name)==1 or name=="space" or name=="tab" or name=="delete" or name=="backspace" or name=="plus":
            self.typing = True
            return True
        self.typing = False
        return True
