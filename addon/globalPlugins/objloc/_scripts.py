# Part of Object Location Tones add-on
# This module implementsa a kind of mixin class that is a part of the GlobalPlugin()
# Its content should be viewed as a continuation of that class from __init__.py
# Methods that are script handlers for the add-on are hosted here
# because the add-ons main class is getting too large for simple maintenance
# and needs some clearing. So, gesture handling script methods are being separated into a mixin style class in their own module.

from baseObject import ScriptableObject
from scriptHandler   import script, getLastScriptRepeatCount
from .posTones       import playCoordinates, playPoints
from .utils          import *
from .geometry       import *
from .UIStrings      import *
import speech
import ui
import wx

__all__ = ["_objlocScriptMethods"]

class _objlocScriptMethods (ScriptableObject):
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
            obj = self._getObject()
            if self.easyTableNav and deps.easyTableNavigator.tableNav:
                obj = o
                r = o.role
                # obj can be an interactive element within the table cell and not the cell itself
                # If so, walk back to the parent object that actually is the cell
                while o and r!=ROLE_TABLECELL and r!=ROLE_DOCUMENT and r!=ROLE_TABLE and r!=ROLE_TABLEROW and r!=ROLE_TABLECOLUMN:
                    o = o.parent
                    r = o.role if o else None
                # Only if we found the cell:
                obj = o if r==ROLE_TABLECELL else obj
            rect  = BBox(obj)
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
            obj = self._getObject()
            level = 0
            for _ in range(count+1):
                if not obj.parent or obj==obj.parent:
                    break
                obj = obj.parent
                level += 1
            if level==0:
                ui.message(MSG_PARENT_NOT_AVAILABLE)
                return
            rect  = BBox(obj)
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
                obj = self._getObject()
                oX, oY = getObjectPos(obj, caret=self.caret)
                mX, mY = getCursorPos()
            except:
                ui.message(MSG_LOCATION_UNAVAILABLE)
                return
            dist = abs(oX-mX) + abs(oY-mY)
            if dist<=self.tolerance:
                playCoordinates(oX, oY, self.duration+150, self.lVolume, self.rVolume, self.stereoSwap)
                ui.message(MSG_MOUSE_ALREADY_THERE)
                return
            self.entered = (mX, mY) in BBox(obj)
            self.startMousePos = (mX, mY)
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
        Plays positional tone for currently focused or navigator object location on demand
        """
        self.DeactivateMouseMonitor()
        try:
            x, y = self._getObjectPos(caret=self.caret)
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

