from api             import getDesktopObject, getNavigatorObject, getFocusObject
from winUser         import getCursorPos
from textInfos       import POSITION_CARET, UNIT_CHARACTER, UNIT_LINE
from speech          import getObjectSpeech
from controlTypes    import ROLE_TERMINAL, ROLE_EDITABLETEXT, ROLE_PASSWORDEDIT, ROLE_DOCUMENT, OutputReason

class LocationError (LookupError):
    """
    An exception raised when unable to retrieve a desired location info from an object.
    """

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

def getObjectDescription (obj):
    return " ".join(x for x in getObjectSpeech(obj, OutputReason.FOCUSENTERED) if isinstance(x, str))
