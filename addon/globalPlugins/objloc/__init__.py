# Object Location Tones
# A global plugin for NVDA
# Copyright 2017-2024 Joseph Lee, released under GPL
# Copyright      2024  Dalen Bernaca, released under GPL

# Brings NVDA Core issue 2559 to life.

import globalPluginHandler
import inputCore

import config
import speech
import ui
import gui
import wx

from scriptHandler import script, getLastScriptRepeatCount
from tones         import beep
from .utils        import *
from .geometry     import *

try:
    from time import monotonic as time
except:
    from time import time

# Some initial values from NVDA configuration
minPitch  = config.conf['mouse']['audioCoordinates_minPitch']
maxPitch  = config.conf['mouse']['audioCoordinates_maxPitch']
maxVolume = config.conf['mouse']['audioCoordinates_maxVolume']

class GlobalPlugin (globalPluginHandler.GlobalPlugin):
    def __init__ (self):
        super(globalPluginHandler.GlobalPlugin, self).__init__()

        self.duration   = 40 # Duration of a positional tone in Msec
        self.volume     = maxVolume # Volume of positional tones in percents
        self.stereoSwap = False # Swap stereo sides
        self.tolerance  = 20   # Mouse to location arrivall detection tolerance
                               # distance between two points in pixels
        self.timeout    = 2    # Timeout to stop the mouse monitoring automatically (in seconds)
        self.caret      = True # Whether to report caret location for editable fields

        self.focusing     = True  # A flag to prevent double beeps on focus of text area children
        self.typing       = False # A flag to prevent beeps during typing
        self.entered      = False # A flag for reporting entering and exiting of the focused object area
        self.processing   = False # A flag to avoid collisions upon fast subsequent keypresses

        self.lastMousePos = (-1, -1) # Used to detect that the mouse stopped moving so that we can stop the timer
        self.lastTime     = 0.0 # Used to detect how much time passed while mouse is stopped
        self.lastKey      = None
        # Mouse monitoring position playing timer
        self.timer = wx.Timer(gui.mainFrame)
        gui.mainFrame.Bind(wx.EVT_TIMER, self._on_mouseMonitor, self.timer)

        # Initial NVDA event bindings
        self.event_becomeNavigatorObject = self._on_becomeNavigatorObject
        self.event_caret = self._on_caret
        inputCore.decide_executeGesture.register(self._on_keyDown)
        self.event_mouseMove = self._on_passThrough

    def terminate (self):
        self.timer.Stop()
        gui.mainFrame.Unbind(wx.EVT_TIMER, handler=self._on_mouseMonitor, source=self.timer)
        inputCore.decide_executeGesture.unregister(self._on_keyDown)

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

    @script(
        gesture="kb:control+Shift+NumpadDelete",
        # Translators: Focused object outline report gesture description in the input gesture dialog
        description=_("Report outline of currently focused object via positional tones."),
        # Translators: Input gestures dialog category for objLocTones.
        category=_("Object Location Tones") )
    def script_objectOutline (self, gesture):
        """
        Plays positional tones for all 4 corners of the object's bounding box.
        If the object is editable, adds a final tone for the caret position.
        """
        try:
            obj = getFocusObject()
            rect = BBox(obj)
            wx.CallAfter(self.playCoordinates, rect.X1, rect.Y1, self.duration+20)
            wx.CallLater(self.duration+220, self.playCoordinates, rect.X2, rect.Y2, self.duration+20)
            wx.CallLater(self.duration+620, self.playCoordinates, rect.X3, rect.Y3, self.duration+20)
            wx.CallLater(self.duration+820, self.playCoordinates, rect.X4, rect.Y4, self.duration+20)
            ui.message(getObjectDescription(obj))
            try:
                if not isEditable(obj):
                    return
                oX, oY = getObjectPos(obj, location=False, caret=True)
                wx.CallLater(self.duration+1120, self.playCoordinates, oX, oY, self.duration+150)
            except:
                pass
        except:
            ui.message(_("Location unavailable"))

    @script(
        gesture="kb:control+Shift+alt+NumpadDelete",
        # Translators: Parent object outline report gesture description in the input gesture dialog
        description=_("Report outline of a parent of currently focused object via positional tones."),
        # Translators: Input gestures dialog category for objLocTones.
        category=_("Object Location Tones") )
    def script_parentObjectOutline (self, gesture):
        """
        Plays positional tones for all 4 corners of the object parent's bounding box.
        """
        if self.processing:
            return
        self.processing = True
        wx.CallLater(500, self.processParentObjectOutline, gesture)

    def processParentObjectOutline (self, gesture):
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
                ui.message("Parent object not available")
                return
            rect = BBox(obj)
            wx.CallAfter(self.playCoordinates, rect.X1, rect.Y1, self.duration+20)
            wx.CallLater(self.duration+220, self.playCoordinates, rect.X2, rect.Y2, self.duration+20)
            wx.CallLater(self.duration+620, self.playCoordinates, rect.X3, rect.Y3, self.duration+20)
            wx.CallLater(self.duration+820, self.playCoordinates, rect.X4, rect.Y4, self.duration+20)
            wx.CallLater(self.duration+840+self.duration, setattr, self, "processing", False)
            ui.message(getObjectDescription(obj)+", ancestor %i" % level)
        except:
            ui.message(_("Location unavailable"))
            self.processing = False

    @script(
        gesture="kb:Shift+NumpadDelete",
        # Translators: The toggle mouse location monitoring gesture description in the input gesture dialog
        description=_("Toggle a mouse cursor position in relation to focused object location reporting via positional tones."),
        # Translators: Input gestures dialog category for objLocTones.
        category=_("Object Location Tones") )
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
                ui.message(_("Location unavailable"))
                return
            dist = abs(oX-mX) + abs(oY-mY)
            if dist<=self.tolerance:
                self.playCoordinates(oX, oY, self.duration+150)
                ui.message(_("Mouse already there"))
                return
            self.event_mouseMove = self._on_mouseMove
            self.timer.Start(200)
            return
        self.timer.Stop()
        self.lastMousePos = (-1, -1)
        self.lastTime = 0.0
        self.event_mouseMove = self._on_passThrough
        speech.cancelSpeech()
        ui.message(_("Mouse location monitoring cancelled"))

    @script(
        gesture="kb:Windows+NumpadDelete",
        # Translators: Input dialog gesture description for on request of mouse cursor location
        description=_("Play a positional tone for a mouse cursor"),
        # Translators: Input gestures dialog category for objLocTones.
        category=_("Object Location Tones") )
    def script_mouse (self, gesture):
        """
        Plays positional tone for a mouse cursor location on demand.
        """
        try:
            x, y = getCursorPos()
            self.playCoordinates(x, y, self.duration+50)
        except:
            pass
        self.timer.Stop()
        self.event_mouseMove = self._on_passThrough
        self.lastMousePos = (-1, -1)
        self.lastTime = 0.0

    @script(
        gesture="kb:NumpadDelete",
        # Translators: The gesture description for on request object location in the input gesture dialog
        description=_("Play a positional tone for currently focused object"),
        # Translators: Input gestures dialog category for objLocTones.
        category=_("Object Location Tones") )
    def script_locate (self, gesture):
        """
        Plays positional tone for currently focused object location on demand
        """
        self.timer.Stop()
        try:
            x, y = getObjectPos(caret=self.caret)
            self.playCoordinates(x, y, self.duration+30)
        except:
            pass

    @script(
        gesture="kb:Control+NumpadDelete",
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
            inputCore.decide_executeGesture.register(self._on_keyDown)
            self.focusing = True
            self.typing = False
            # Translators: Message when positional tones are switched on
            ui.message(_("Positional tones on"))
            return
        self.event_becomeNavigatorObject = self._on_passThrough
        self.event_caret = self._on_passThrough
        inputCore.decide_executeGesture.register(self._on_keyDown)
        self.timer.Stop()
        self.event_mouseMove = self._on_passThrough
        self.lastMousePos = (-1, -1)
        self.lastTime = 0.0
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
            # Skip a beep right after text area gained focus
            self.focusing = False
            nextHandler()
            return
        tei = obj.makeTextInfo(POSITION_CARET)
        tei.expand(UNIT_CHARACTER)
        try:
            x, y = tei.pointAtStart
            print((x, y))
            self.playCoordinates(x+3, y+8)
        except LookupError:
            tei.collapse(end=True)
            tei.move(UNIT_CHARACTER, -1)
            eol, y = tei.pointAtStart
            tei.expand(UNIT_LINE)
            sol, y = tei.pointAtStart
            x = eol+5 if self.lastKey.endswith("end") else sol
            empty = not bool("".join(tei.text.splitlines()))
            x = x if empty else sol
            if not self.lastKey.endswith("end") and empty:
                y += 32
            print(("z", x, y))
            self.playCoordinates(x+3, y+8)
        except Exception as e:
            print("%s(%s)" % (e.__class__.__name__, str(e)))
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
            ui.message(_("Location unavailable"))
            return
        # If mouse is stationary for too long, automatically stop monitoring:
        t   = time()
        lmp = self.lastMousePos
        if lmp==mp and t-self.lastTime>=self.timeout:
            self.lastMousePos = (-1, -1)
            self.lastTime     = 0.0
            self.timer.Stop()
            self.event_mouseMove = self._on_passThrough
            ui.message(_("Mouse location monitoring stopped"))
            return
        if lmp!=mp:
            self.lastMousePos = mp
            self.lastTime = t
        wx.CallAfter(self.playCoordinates, mp[0], mp[1], self.duration+40)
        wx.CallLater(self.duration+100, self.playCoordinates, oX, oY, self.duration+70)

    def _on_mouseMove (self, obj, nextHandler, x, y):
        """
        Event used during mouse monitoring that checks for the current
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
            ui.message(_("Location unavailable"))
            nextHandler()
            return
        if (x, y) in BBox(fobj):
            if not self.entered:
                self.entered = True
                speech.cancelSpeech()
                ui.message(_("Entering focused object"))
        else:
            if self.entered:
                speech.cancelSpeech()
                ui.message(_("Exiting focused object"))
            self.entered = False
        dist = abs(oX-x) + abs(oY-y)
        if dist<=self.tolerance:
            self.playCoordinates(oX, oY, self.duration+150)
            self.timer.Stop()
            self.event_mouseMove = self._on_passThrough
            self.lastMousePos = (-1, -1)
            self.lastTime     = 0.0
            speech.cancelSpeech()
            ui.message(_("Location reached"))
        nextHandler()

    event_mouseMove = _on_passThrough

    def _on_keyDown (self, gesture):
        """
        Notifies other relevant methods that typing has taken  place.
        """
        name = gesture.mainKeyName
        self.lastKey = name
        if len(name)==1 or name=="space" or name=="tab" or name=="delete" or name=="backspace" or name=="plus":
            self.typing = True
            return True
        self.typing = False
        return True
