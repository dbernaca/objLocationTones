from .meta import AutoAll

__all__ = AutoAll(globals())

from languageHandler import installedTranslation
from textInfos              import POSITION_CARET, POSITION_FIRST, UNIT_CHARACTER, UNIT_LINE

__all__.begin()
from api          import getDesktopObject, getNavigatorObject, getFocusObject, getForegroundObject
from winUser      import getCursorPos
from speech       import getObjectSpeech
from controlTypes import ROLE_TERMINAL, ROLE_EDITABLETEXT, ROLE_RICHEDIT, ROLE_PASSWORDEDIT, ROLE_DOCUMENT, ROLE_TABLE, ROLE_TABLECELL, ROLE_TABLEROW, ROLE_TABLECOLUMN, STATE_MULTILINE, OutputReason
__all__.end()
from api                     import isTypingProtected, getCaretPosition as getCaretTextInfo
from winAPI._displayTracking import displayChanged
from treeInterceptorHandler  import DocumentTreeInterceptor
from globalCommands          import GlobalCommands, commands
from functools               import update_wrapper, WRAPPER_ASSIGNMENTS
from gui.settingsDialogs     import MouseSettingsPanel, NVDASettingsDialog
from .settings.objects       import Flag
import config, ui

gettext = installedTranslation().gettext

__all__.begin()

class LocationError (LookupError):
    """
    An exception raised when unable to retrieve a desired location info from an object.
    """

def isEditable (obj):
    """
    Returns True if the *obj* is an editable field, False otherwise.
    """
    if obj:
        r = obj.role
        return r==ROLE_EDITABLETEXT or r==ROLE_RICHEDIT or r==ROLE_PASSWORDEDIT or r==ROLE_TERMINAL or r==ROLE_DOCUMENT
    return False

def isMultiline (obj):
    """
    Returns True if the *obj* is a multiline editable field, False otherwise.
    """
    return STATE_MULTILINE in obj.states

def getCaretPos (obj=None):
    try:
        obj = obj or getFocusObject()
        r = obj.role
        if r!=ROLE_EDITABLETEXT and r!=ROLE_RICHEDIT and r!=ROLE_PASSWORDEDIT and r!=ROLE_TERMINAL and r!=ROLE_DOCUMENT:
            raise LocationError("Not an editable")
        ti = obj.treeInterceptor
        if isinstance(ti, DocumentTreeInterceptor) and not ti.passThrough:
            obj = ti
        try:
            tei = obj.makeTextInfo(POSITION_CARET)
            tei.expand(UNIT_CHARACTER)
        except (NotImplementedError, RuntimeError):
            tei = obj.makeTextInfo(POSITION_FIRST)
        try:
            return tei.pointAtStart
        except LookupError:
            # Caret at the very end of document
            try:
                tei.collapse(end=True)
                tei.move(UNIT_CHARACTER, -1)
                endOfLine, prevLine = tei.pointAtStart
            except:
                # Empty document
                return (obj.location[0]+7, obj.location[1]+43)
            tei.expand(UNIT_LINE)
            startOfLine, line = tei.pointAtStart
            text = tei.text
            if text[-2:-1] in "\r\n":
                # There is an empty line at the end of document
                # on which we tried the caret position extraction
                return startOfLine, prevLine+32
            # Otherwise, the last line is really the last line
            return endOfLine+16, prevLine
    except LocationError:
        raise
    except:
        raise LocationError("Location unavailable")

def getCharacterAtCaret ():
    if isTypingProtected():
        return ""
    try:
        info = getCaretTextInfo().copy()
        info.expand(UNIT_CHARACTER)
        return info.text
    except (RuntimeError, NotImplementedError):
        return ""

def getCharacterBeforeCaret ():
    try:
        info = getCaretTextInfo().copy()
        info.collapse()
        if info.move(UNIT_CHARACTER, -1) == 0:
            return ""
        info.expand(UNIT_CHARACTER)
        ch = info.text
        return "*" if isTypingProtected() and ch else ch
    except (RuntimeError, NotImplementedError, LookupError):
        return ""

def getObjectPos (obj=None, location=True, caret=False):
    """
    Returns x and y coordinates of the obj.
    The obj argument is an object you wish to get the position for, or None (default).
    If None, api.getNavigatorObject() is used to get the object to use.
    If caret argument is True (defaults to False), function will return position of the caret
    but only if the obj is considered editable. If location is False (defaults to True),
    and caret position is unavailable, then the centroid location of the editable
    will be returned instead. In all other circumstances
    the coordinates x, y of the center of mass for the
    obj will be returned, and, if not available, LocationError()
    will be raised.
    """
    try:
        obj = obj or getNavigatorObject()
        if caret:
            try:
                return getCaretPos(obj)
            except:
                if not location:
                    raise
        l = obj.location
        return (l[0]+(l[2]//2), l[1]+(l[3]//2))
    except LocationError:
        raise
    except:
        raise LocationError("Location unavailable")

getObjectPosCenter = getObjectPos

def getObjectPosLeft (obj=None, location=True, caret=False):
    """
    Returns x and y coordinates of the obj, for its left border.
    The left border is considered a point where x coordinate represents the beginning of the object and y its middle.
    The obj argument is an object you wish to get the position for, or None (default).
    If None, api.getNavigatorObject() is used to get the object to use.
    If caret argument is True (defaults to False), function will return position of the caret
    but only if the obj is considered editable. If location is False (defaults to True),
    and caret position is unavailable, then the left border location of the editable
    will be returned instead. In all other circumstances
    the coordinates x, y of the left border for the
    obj will be returned, and, if not available, LocationError()
    will be raised.
    """
    try:
        obj = obj or getNavigatorObject()
        if caret:
            try:
                return getCaretPos(obj)
            except:
                if not location:
                    raise
        l = obj.location
        return (l[0], l[1]+(l[3]//2))
    except LocationError:
        raise
    except:
        raise LocationError("Location unavailable")

def getObjectPosRight (obj=None, location=True, caret=False):
    """
    Returns x and y coordinates of the obj, for its right border.
    The right border is considered a point where x coordinate represents the ending of the object and y its middle.
    The obj argument is an object you wish to get the position for, or None (default).
    If None, api.getNavigatorObject() is used to get the object to use.
    If caret argument is True (defaults to False), function will return position of the caret
    but only if the obj is considered editable. If location is False (defaults to True),
    and caret position is unavailable, then the right border location of the editable
    will be returned instead. In all other circumstances
    the coordinates x, y of the right border for the
    obj will be returned, and, if not available, LocationError()
    will be raised.
    """
    try:
        obj = obj or getNavigatorObject()
        if caret:
            try:
                return getCaretPos(obj)
            except:
                if not location:
                    raise
        l = obj.location
        return (l[0]+l[2], l[1]+(l[3]//2))
    except LocationError:
        raise
    except:
        raise LocationError("Location unavailable")

def getObjectDescription (obj):
    return " ".join(x for x in getObjectSpeech(obj, OutputReason.FOCUSENTERED) if isinstance(x, str))

def getObjectRoleName (obj):
    try:
        return obj.role.displayString
    except:
        return ""

def getKeyName (gesture):
    """
    Retrieves a full display key name from a gesture without involving locales.
    Note: The gesture needs to be KeyboardInputGesture() compatible or AttributeError will be raised.
    """
    if gesture:
        name = gesture.mainKeyName
        mods = "+".join(gesture.modifierNames)
        return (name if mods=="shift" and (len(name)==1 or name=="plus") else mods+"+"+name) if mods else name

def willEnterText (gesture, obj=None):
    """
    Returns True if the gesture will affect the text editables passed by obj.
    False is returned if obj is not a text editable.
    If obj is not given at all, getFocusObject() will be used to get it.

    gesture._get_isCharacter() has a bug around "+" key so gesture.isCharacter cannot be used and we need this function.
    Note: The gesture needs to be KeyboardInputGesture() compatible or AttributeError will be raised.
    """
    try:
        obj = obj or getFocusObject()
        r = obj.role if obj else None
    except Exception as e:
        # This should never occur any longer. It caused problems if called not from main thread, but just in case...
        print("Error in critical moment. This might be effecting normal navigation. Please contact the Object Location Tones add-on maintainer immediately.")
        print("If you are experiencing problems during navigation, disable positional tones while working in this area.")
        print("Exception is: "+str(e))
        return False
    if not (r==ROLE_EDITABLETEXT or r==ROLE_RICHEDIT or r==ROLE_PASSWORDEDIT or r==ROLE_TERMINAL or r==ROLE_DOCUMENT):
        return False
    name = gesture.mainKeyName
    return len(name)==1 or name=="space" or name=="tab" or name=="delete" or name=="backspace" or name=="plus"

__all__.end()

class Display:
    """
    Represents one display connected to your machine.
    """
    __slots__ = ("top", "left", "width", "height", "size", "primary")
    def __init__ (self, top, left, width, height):
        self.top     = top
        self.left    = left
        self.width   = width
        self.height  = height
        self.primary = False
        self.size    = (width, height)

    def getSize (self):
        return self.size

class DisplayLayout:
    __slots__ = ("primary", "getPrimaryDisplaySize", "__weakref__")
    def __init__ (self):
        self.primary = pd = Display(*getDesktopObject().location)
        pd.primary = True
        self.getPrimaryDisplaySize = pd.getSize

    def refresh (self, orientationState=None):
        pd = self.primary
        pd.__init__(*getDesktopObject().location)
        pd.primary = True

    def enableAutoRefresh (self):
        displayChanged.register(self.refresh)

    def disableAutoRefresh (self):
        displayChanged.unregister(self.refresh)

DisplayLayout = DisplayLayout()

class MouseTracking:
    """
    This class is in charge of protecting NVDA's mouse tracking feature during the mouse monitoring.
    While Object Location Tones is performing the mouse monitoring, it needs mouse tracking.
    So this class will automatically, and temporarily, enable it if it is disabled and monitoring is requested.
    And will prevent user from disabling it while mouse monitoring is in progress.
    This involves disabling the script activated via gesture and adjusting the MouseSettingsPanel() to respect
    Object Location Tones' needs.
    """
    class MouseSettings (MouseSettingsPanel):
        """
        This class replaces the original MouseSettingsPanel() with a version that enables user to change the mouse tracking option,
        but if the mouse monitoring is in progress it will not interfere with its working by disabling the tracking immediately after user presses OK or Apply.
        Instead, the config will revert to user's chosen option after monitoring ends.
        """
        # This flag can be locked so that it shows always the same value (last one set)
        # while, at the same time, it enables behind the scene setting and clearing, and after unlocking it
        # the value from memory becomes the main value.
        # Thus we can lock the config to True, while allowing users to change the value, which will be applied when we do not need the monitoring any longer
        mouseTrackingEnabled = Flag(config.conf["mouse"]["enableMouseTracking"])
        # Bind to class namespace for faster and neater access
        lock    = mouseTrackingEnabled.lock
        unlock  = mouseTrackingEnabled.unlock
        flagSet = mouseTrackingEnabled.set
        flagClr = mouseTrackingEnabled.clear
        flagTog = mouseTrackingEnabled.toggle
        def makeSettings(self, settingsSizer):
            MouseSettingsPanel.makeSettings(self, settingsSizer)
            self.mouseTrackingCheckBox.SetValue(self.mouseTrackingEnabled.memory)

        def onSave (self):
            MouseSettingsPanel.onSave(self)
            # It is OK if config reflects False for a moment while monitoring, it will not have concrete impact on the add-on's working
            mte = self.mouseTrackingEnabled
            mte.set() if self.mouseTrackingCheckBox.IsChecked() else mte.clear()
            config.conf["mouse"]["enableMouseTracking"] = mte.value

        @classmethod
        def set (cls):
            cls.lock(True)
            cls.flagSet() if config.conf["mouse"]["enableMouseTracking"] else cls.flagClr()
            config.conf["mouse"]["enableMouseTracking"] = True

        @classmethod
        def clear (cls):
            config.conf["mouse"]["enableMouseTracking"] = cls.unlock()

    def __init__ (self, replacement=(lambda instance, gesture: None)):
        self._oldToggleMouseTrackingScript   = scr = commands.script_toggleMouseTracking
        self._oldToggleMouseTrackingGestures = self.getGestures(scr)
        self.replacement = replacement
        self._mouseTrackingEnsured         = False
        self._assignments = WRAPPER_ASSIGNMENTS+('gestures', 'category', 'allowInSleepMode', 'bypassInputHelp', 'canPropagate', 'speakOnDemand')
        self._updater = update_wrapper

    def injectSettingsPanel (self):
        mouse = NVDASettingsDialog.categoryClasses.index(MouseSettingsPanel)
        NVDASettingsDialog.categoryClasses[mouse] = self.MouseSettings

    def retractSettingsPanel (self):
        mouse = NVDASettingsDialog.categoryClasses.index(self.MouseSettings)
        NVDASettingsDialog.categoryClasses[mouse] = MouseSettingsPanel

    def getGestures (self, script):
        gmitems = commands._gestureMap.items()
        scrName = script.__qualname__
        return [k for k, v in gmitems if v.__qualname__==scrName]

    def ensure (self):
        if self._mouseTrackingEnsured:
            return
        self._oldToggleMouseTrackingScript = scr = commands.script_toggleMouseTracking
        self._oldToggleMouseTrackingGestures = gestures = self.getGestures(scr)
        GlobalCommands.script_toggleMouseTracking = self._updater(self.replacement,
                             scr, self._assignments)
        for gesture in gestures:
            commands.bindGesture(gesture, "toggleMouseTracking")
        self.MouseSettings.set()
        self._mouseTrackingEnsured = True

    def restore (self):
        if not self._mouseTrackingEnsured:
            return
        GlobalCommands.script_toggleMouseTracking = scr = self._oldToggleMouseTrackingScript
        for gesture in self._oldToggleMouseTrackingGestures:
            commands.bindGesture(gesture, "toggleMouseTracking")
        self.MouseSettings.clear()
        self._mouseTrackingEnsured = False

__all__.begin()

MouseTracking = MouseTracking()
__all__.end()
def toggleMouseTracking (instance, gesture):
    switch = MouseTracking.MouseSettings.flagTog()
    msg = gettext("Mouse tracking on") if switch else gettext("Mouse tracking off")
    ui.message(msg)
MouseTracking.replacement = toggleMouseTracking

__all__.begin()
ensureMouseTracking   = MouseTracking.ensure
restoreMouseTracking  = MouseTracking.restore
getPrimaryDisplaySize = DisplayLayout.getPrimaryDisplaySize

__all__.end().finalize()

