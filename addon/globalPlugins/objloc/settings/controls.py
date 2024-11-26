"""
Part of Object Location Tones settings package.

Implements GUI controls for use in NVDA settings panel.
These custom controls are tailored to prevent wrong input and/or to return correct datatypes.
"""

from gui.nvdaControls import EnhancedInputSlider as SliderCtrl
import wx

class IntCtrl (wx.TextCtrl):
    """
    Lets user type in an integer between -inf and inf.
    Any other input is not possible.
    The initial value is mandatory.
    The GetValue() method returns an integer or,
    if user leaves the field empty, the initial value.
    That is, if the field is left empty, the value is not considered changed.
    """
    def __init__ (self, *args, **kwargs):
        wx.TextCtrl.__init__(self, *args, **kwargs)
        self.Bind(wx.EVT_CHAR, self.OnChar)
        self.OriginalValue = wx.TextCtrl.GetValue(self)

    def OnChar (self, e):
        key = e.GetKeyCode()
        if chr(key) in "1234567890":
            e.Skip()
        elif chr(key)=="-":
            # A minus can be only one, and only at the beginning
            v = wx.TextCtrl.GetValue(self)
            if v.count("-"):
                return wx.Bell()
            if not self.GetInsertionPoint():
                return e.Skip()
            wx.Bell()
        # Support navigation and deletions
        elif key in (wx.WXK_LEFT, wx.WXK_RIGHT, wx.WXK_DELETE, wx.WXK_BACK):
            e.Skip()
        else:
            wx.Bell()

    def GetValue (self):
        v = wx.TextCtrl.GetValue(self)
        try:
            return int(v)
        except:
            return int(self.OriginalValue)

class FloatCtrl (wx.TextCtrl):
    """
    Lets user type in a float between -inf and inf.
    Any other input is not possible.
    The initial value is mandatory.
    The GetValue() method returns a float or,
    if user leaves the field empty, the initial value.
    That is, if the field is left empty, the value is not considered changed.
    """
    def __init__ (self, *args, **kwargs):
        wx.TextCtrl.__init__(self, *args, **kwargs)
        self.Bind(wx.EVT_CHAR, self.OnChar)
        self.OriginalValue = wx.TextCtrl.GetValue(self)

    def OnChar (self, e):
        key = e.GetKeyCode()
        if chr(key) in "1234567890":
            e.Skip()
        elif chr(key)=="-":
            # A minus can be only one, and only at the beginning
            v = wx.TextCtrl.GetValue(self)
            if v.count("-"):
                return wx.Bell()
            if not self.GetInsertionPoint():
                return e.Skip()
            wx.Bell()
        elif key in (wx.WXK_LEFT, wx.WXK_RIGHT, wx.WXK_DELETE, wx.WXK_BACK):
            e.Skip()
        elif chr(key)==".":
            # A decimal point can be only one
            if wx.TextCtrl.GetValue(self).count(".")==0:
                e.Skip()
            else:
                wx.Bell()
        else:
            wx.Bell()

    def GetValue (self):
        v = wx.TextCtrl.GetValue(self)
        try:
            return float(v)
        except:
            return float(self.OriginalValue)
