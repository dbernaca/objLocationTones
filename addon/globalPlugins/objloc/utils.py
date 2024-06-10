from api                    import getDesktopObject, getNavigatorObject, getFocusObject
from winUser                import getCursorPos
from textInfos              import POSITION_CARET, POSITION_FIRST, UNIT_CHARACTER, UNIT_LINE
from speech                 import getObjectSpeech
from controlTypes           import ROLE_TERMINAL, ROLE_EDITABLETEXT, ROLE_PASSWORDEDIT, ROLE_DOCUMENT, OutputReason
from treeInterceptorHandler import DocumentTreeInterceptor

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

def getCaretPos (obj=None):
    try:
        obj = obj or getFocusObject()
        r = obj.role
        if r!=ROLE_EDITABLETEXT and r!=ROLE_PASSWORDEDIT and r!=ROLE_TERMINAL and r!=ROLE_DOCUMENT:
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

def getObjectDescription (obj):
    return " ".join(x for x in getObjectSpeech(obj, OutputReason.FOCUSENTERED) if isinstance(x, str))
