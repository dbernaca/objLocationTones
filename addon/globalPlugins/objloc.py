# Object Location Tones
# A global plugin for NVDA
# Copyright 2017-2024 Joseph Lee, released under GPL
# Copyright      2024  Dalen Bernaca, released under GPL

# Brings NVDA Core issue 2559 to life.

import globalPluginHandler
import scriptHandler

import config
import speech
import ui
import gui
import wx

from tones        import beep
from api          import getDesktopObject, getNavigatorObject, getFocusObject
from textInfos    import POSITION_CARET
from winUser      import getCursorPos
from controlTypes import ROLE_TERMINAL, ROLE_EDITABLETEXT, ROLE_PASSWORDEDIT, ROLE_DOCUMENT

try:
    from time import monotonic as time
except:
    from time import time

class LocationError (Exception):
    """
    An exception raised when unable to retrieve a desired location info from an object.
    """

# Some initial values from NVDA configuration
minPitch  = config.conf['mouse']['audioCoordinates_minPitch']
maxPitch  = config.conf['mouse']['audioCoordinates_maxPitch']
maxVolume = config.conf['mouse']['audioCoordinates_maxVolume']

def isEditable (obj):
    """
    Returns True if the *obj* is an editable field, False otherwise.
    """
    r = obj.role
    return r==ROLE_EDITABLETEXT or r==ROLE_PASSWORDEDIT or r==ROLE_TERMINAL or r==ROLE_DOCUMENT

def getObjectPos (obj=None, location=True, caret=False):
    """
    Returns x and y coordinates of the obj.
    The obj argument is an object you wish to get the position for, or None (default).
    If None, api.getFocusObject() is used to get the object to use.
    If caret argument is True (defaults to False), function will return position of the caret
    in case the obj is considered editable. If location is False (defaults to True),
    and caret position is unavailable, then the centroid location of the editable
    will be returned instead. In all other circumstances
    the coordinates x, y of the center of mass for the
    obj will be returned, and, if not available, LocationError()
    will be raised.
    """
    try:
        obj = obj or getFocusObject()
        if caret:
            try:
                r = obj.role
                if r==ROLE_EDITABLETEXT or r==ROLE_PASSWORDEDIT or r==ROLE_TERMINAL or r==ROLE_DOCUMENT:
                    tei = obj.makeTextInfo(POSITION_CARET)
                    return tei.pointAtStart
            except:
                if not location:
                    raise
        l = obj.location
        return (l[0]+(l[2]//2), l[1]+(l[3]//2))
    except:
        pass
    raise LocationError("Location unavailable")

class BBox (object):
    """
    Class for dealing with more complex information of object locations.
    And providing potential operations regarding the same.
    """
    __slots__ = ("L", "T", "W", "H", "X1", "X2", "X3", "X4", "Y1", "Y2", "Y3", "Y4", "TL", "TR", "BR", "BL", "corners")
    def __init__ (self, obj):
        """
        Takes an object and initializes its bounding box.
        """
        loc = obj.location
        self.L, self.T, self.W, self.H = loc
        # Left top corner
        self.X1 = x1 = loc[0]
        self.Y1 = y1 = loc[1]
        self.TL = (x1, y1)
        # Right top corner
        self.X2 = x2 = loc[0]+loc[2]
        self.Y2 = y2 = loc[1]
        self.TR = (x2, y2)
        # Right bottom corner
        self.X3 = x3 = loc[0]+loc[2]
        self.Y3 = y3 = loc[1]+loc[3]
        self.BR = (x3, y3)
        # Left Bottom corner
        self.X4 = x4 = loc[0]
        self.Y4 = y4 = loc[1]+loc[3]
        self.BL = (x4, y4)
        self.corners = ((x1, y1), (x2, y2), (x3, y3), (x4, y4))

    def __contains__ (self, obj):
        """
        Checks whether a point (x, y) or a BBox() of an obj or obj itself given by argument obj,
        occupies the space bounded by this bounding box.
        Returns True if this BBox() and the operand obj share any points between them,
        False otherwise. Intended use is, for example:
        (10, 10) in BBox(obj)
        """
        if isinstance(obj, tuple):
            return (self.X1 <= obj[0] <= self.X2) and (self.Y1 <= obj[1] <= self.Y4)
        obj = obj if isinstance(obj, BBox) else BBox(obj)
        return any((xy in self) for xy in obj.corners)

class GlobalPlugin (globalPluginHandler.GlobalPlugin):
    def __init__ (self):
        super(globalPluginHandler.GlobalPlugin, self).__init__()

        self.duration   = 40 # Duration of a positional tone in Msec
        self.volume     = maxVolume # Volume of positional tones in percents
        self.stereoSwap = False # Swap stereo sides
        self.tolerance  = 20 # Mouse to location arrivall detection tolerance
                             # distance between two points in pixels
        self.timeout    = 2 # Timeout to stop the mouse monitoring (in seconds)
        self.caret      = True # Whether to report caret location for editable fields

        self.focusing     = True # A flag to prevent double beeps on focus of text area children
        self.entered      = False # A flag for reporting entering and exiting of the focused object area

        self.lastMousePos = (-1, -1) # Used to detect that the mouse stopped moving so that we can stop the timer
        self.lastTime     = 0.0 # Used to detect how much time passed while mouse is stopped

        # Mouse monitoring position playing timer
        self.timer = wx.Timer(gui.mainFrame, wx.ID_ANY)
        gui.mainFrame.Bind(wx.EVT_TIMER, self._on_mouseMonitor, self.timer)

        # Initial NVDA event bindings
        self.event_becomeNavigatorObject = self._on_becomeNavigatorObject
        self.event_caret = self._on_caret
        self.event_mouseMove = self._on_passThrough

    def terminate (self):
        self.timer.Stop()
        gui.mainFrame.Unbind(wx.EVT_TIMER, self._on_mouseMonitor, self.timer)

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
        # Translators: Object outline report gesture description in the input gesture dialog
        description=_("Report focused object's outline via positional tones."),
        # Translators: Input gestures dialog category for objLocTones.
        category=_("Object Location Tones") )
    def script_objectOutline (self, gesture):
        """
        Plays positional tones for all 4 corners of the object's bounding box.
        If the object is editable, adds final tone for the caret position.
        """
        try:
            obj = getFocusObject()
            rect = BBox(obj)
            wx.CallAfter(self.playCoordinates, rect.X1, rect.Y1, self.duration+20)
            wx.CallLater(self.duration+220, self.playCoordinates, rect.X2, rect.Y2, self.duration+20)
            wx.CallLater(self.duration+620, self.playCoordinates, rect.X3, rect.Y3, self.duration+20)
            wx.CallLater(self.duration+820, self.playCoordinates, rect.X4, rect.Y4, self.duration+20)
            try:
                if not isEditable(obj):
                    return
                oX, oY = getObjectPos(obj, location=False, caret=True)
                wx.CallLater(self.duration+1120, self.playCoordinates, oX, oY, self.duration+150)
            except:
                pass
        except:
            ui.message(_("Location unavailable"))

    @scriptHandler.script(
        # Translators: The toggle mouse location monitoring gesture description in the input gesture dialog
        description=_("Toggle a mouse cursor position in relation to navigator object location reporting via positional tones."),
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

    @scriptHandler.script(
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

    @scriptHandler.script(
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