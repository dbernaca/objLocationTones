# Part of Object Location Tones add-on
# This module implementsa a kind of mixin class that is a part of the GlobalPlugin()
# Its content should be viewed as a continuation of that class from __init__.py
# Methods that are event handlers for the add-on are hosted here
# because the add-ons main class is getting too large for simple maintenance
# and needs some clearing. So, event handler methods are being separated into a mixin style class in their own module.

from keyboardHandler import KeyboardInputGesture
from .utils          import *
from .UIStrings      import MSG_LOCATION_REACHED, MSG_LOCATION_UNAVAILABLE, MSG_ENTERING, MSG_EXITING, MSG_MOUSE_MONITOR_STOPPED
from .geometry       import BBox
from .posTones       import playCoordinates, playPoints
from .constants      import *
from time            import monotonic as time
import wx
import ui
import speech

__all__ = ["_objlocEventMethods"]

class _objlocEventMethods:
    def _on_passThrough (self, obj, nextHandler, *args, **kwargs):
        """
        An event handler that just passes the event to the next handler and does nothing else.
        Used to swap a real handler when switching off a feature.
        NVDA does not use event mapping to pre-map available events,
        instead it uses hasattr() and try-except to test for availability at runtime.
        This means we can just delete an event attribute to switch off a feature,
        but replacing them with the dummy event handler instead achieves:
        1. Possible better performance in cases where try-except is involved
        2. Preparation for the day NV Access does implement event mapping to make NVDA even more efficient
        3. Perhaps a little bit cleaner, more understandable code
        """
        nextHandler()

    # event_foreground handlers
    # They use processing and focusing control flow attributes from the main class
    # caret attribute managed via settings and lastForeground data attribute

    def processForeground (self):
        try:
            obj = self.lastForeground or getForegroundObject()
            rect  = BBox(obj)
            after = playPoints(200, rect.corners, self.duration+20, self.lVolume, self.rVolume, self.stereoSwap)
            if self.caret:
                try:
                    oX, oY = getCaretPos(obj)
                    wx.CallLater(after+40, playCoordinates, oX, oY, self.durationCaret+150, self.lVolume, self.rVolume, self.stereoSwap)
                    wx.CallLater(after+50, setattr, self, "processing", False)
                except:
                    wx.CallLater(after+10, setattr, self, "processing", False)
            else:
                wx.CallLater(after+10, setattr, self, "processing", False)
            self.focusing = True # Prevent tone in caret event if foreground played successfully
        except:
            self.processing = False

    def _on_foreground (self, obj, nextHandler):
        try:
            nextHandler()
        finally:
            if self.processing:
                return
            self.processing = True
            self.lastForeground = obj
            wx.CallLater(150, self.processForeground)

    def _on_navigation (self, obj, nextHandler, *args, **kwargs):
        """
        Event handler that plays a positional tone upon navigation.
        """
        self.focusing = True # Prevent tone in the caret event right after text area gains focus
        if self.processing:
            nextHandler()
            return
        try:
            x, y = self._getObjectPos(obj, caret=self.caret)
            playCoordinates(x, y, self.duration, self.lVolume, self.rVolume, self.stereoSwap)
        except:
            pass
        nextHandler()

    def _on_caret (self, obj, nextHandler):
        """
        Event handler that plays a positional tone upon caret movements.
        """
        if self.focusing:
            # Skip a caret tone right after text area gained focus because becomeNavigator or gainFocus fires first
            self.focusing = False
            nextHandler()
            return
        if self.typing:
            # Caret moved because user is typing or editing the text:
            if not self.caretTyping:
                nextHandler()
                return
            try:
                x, y = getCaretPos(obj)
                playCoordinates(x, y, self.durationCaret, self.lVolume, self.rVolume, self.stereoSwap)
            except:
                pass
            nextHandler()
            return
        if self.caretMode==CARET_NONE:
            # Do not report movements is selected
            nextHandler()
            return
        # Caret navigation:
        name = getKeyName(self.lastKey)
        if self.caretMode==CARET_VERTICAL and name not in ("upArrow", "downArrow", "pageUp", "pageDown", "enter", "control+home", "control+end"):
            # Vertical navigation
            pass
        elif self.caretMode==CARET_HORIZONTAL and name not in ("leftArrow", "rightArrow", "home", "end"):
            # Horizontal navigation
            pass
        else:
            try:
                x, y = getCaretPos(obj)
                playCoordinates(x, y, self.durationCaret, self.lVolume, self.rVolume, self.stereoSwap)
            except:
                pass
        nextHandler()

    def _on_mouseMonitor (self, e):
        """
        Timer callback to play positional tones of a mouse cursor location and the current reference point.
        Helps to monitor their relation, i.e. difference of their distance on the screen.
        """
        try:
            mp     = getCursorPos()
            obj = self._getObject()
            oX, oY = getObjectPos(obj, caret=self.caret)
        except:
            self.DeactivateMouseMonitor()
            ui.message(MSG_LOCATION_UNAVAILABLE)
            return
        # If mouse is stationary for too long, automatically stop monitoring:
        t   = time()
        lmp = self.lastMousePos
        if lmp==mp and t-self.lastTime>=self.timeout:
            self.DeactivateMouseMonitor()
            if self.stopMessage:
                ui.message(MSG_MOUSE_MONITOR_STOPPED)
            return
        if lmp!=mp:
            self.lastMousePos = mp
            self.lastTime = t
        wx.CallAfter(playCoordinates, mp[0], mp[1], self.duration+40, self.lVolume, self.rVolume, self.stereoSwap)
        if self.refPoint==MOUSE_REF_FOCUS or self.refPoint==MOUSE_REF_NAVIGATOR:
            # Play focused or navigator objects pos as a ref point
            wx.CallLater(self.duration+100, playCoordinates, oX, oY, self.duration+70, self.lVolume, self.rVolume, self.stereoSwap)
        elif self.refPoint==MOUSE_REF_TLW:
            # Top left of the foreground window
            try:
                wlpx, wlpy, _, _ = getForegroundObject().location
            except:
                return
            wx.CallLater(self.duration+100, playCoordinates, wlpx, wlpy, self.duration+70, self.lVolume, self.rVolume, self.stereoSwap)
        elif self.refPoint==MOUSE_REF_CW:
            # Center of the foreground window
            try:
                wcpx, wcpy = getForegroundObject().location.center
            except:
                return
            wx.CallLater(self.duration+100, playCoordinates, wcpx, wcpy, self.duration+70, self.lVolume, self.rVolume, self.stereoSwap)
        elif self.refPoint==MOUSE_REF_TLS:
            # Top left corner of the screen, that is (0, 0)
            wx.CallLater(self.duration+100, playCoordinates, 0, 0, self.duration+70, self.lVolume, self.rVolume, self.stereoSwap)
        elif self.refPoint==MOUSE_REF_CS:
            # Center of the virtual screen as given by the desktop object
            try:
                dcpx, dcpy = getDesktopObject().location.center
            except:
                return
            wx.CallLater(self.duration+100, playCoordinates, dcpx, dcpy, self.duration+70, self.lVolume, self.rVolume, self.stereoSwap)
        elif self.refPoint==MOUSE_REF_START:
            pspx, pspy = self.startMousePos
            wx.CallLater(self.duration+100, playCoordinates, pspx, pspy, self.duration+70, self.lVolume, self.rVolume, self.stereoSwap)
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
            fobj = self._getObject()
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
            self.entered = (x, y) in BBox(self._getObject())
        except:
            pass
        self.startMousePos = (x, y)
        self.ActivateMouseMonitor()
        nextHandler()

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

    def _on_easyTableNav (self, obj, event=None):
        try:
            o = getNavigatorObject() # getFocusObject() or using obj argument, does not work as well as it should
            r = o.role
            # Navigator can be an interactive element within the table cell and not the cell itself
            # If so, walk down to the parent object that actually is the cell
            while o and r!=ROLE_TABLECELL and r!=ROLE_DOCUMENT and r!=ROLE_TABLE and r!=ROLE_TABLEROW and r!=ROLE_TABLECOLUMN:
                o = o.parent
                r = o.role if o else None
            if r!=ROLE_TABLECELL:
                # If we ended somewhere in the middle of nowhere, just do not play the coordinates
                return
            x, y = self._getObjectPos(o, caret=False)
            playCoordinates(x, y, self.duration, self.lVolume, self.rVolume, self.stereoSwap)
        except:
            pass

    event_foreground = _on_foreground

    event_becomeNavigatorObject = _on_navigation

    event_gainFocus = _on_passThrough

    event_caret = _on_passThrough

    event_mouseMove = _on_passThrough
