import wx

class IntCtrl (wx.TextCtrl):
    def __init__ (self, *args, **kwargs):
        wx.TextCtrl.__init__(self, *args, **kwargs)
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def OnChar (self, e):
        key = e.GetKeyCode()
        if chr(key) in "1234567890":
            e.Skip()
        elif chr(key)=="-":
            v = wx.TextCtrl.GetValue(self)
            if v.count("-"):
                return wx.Bell()
            if not self.GetInsertionPoint():
                return e.Skip()
            wx.Bell()
        elif key in (wx.WXK_LEFT, wx.WXK_RIGHT, wx.WXK_DELETE, wx.WXK_BACK):
            e.Skip()
        else:
            wx.Bell()

class FloatCtrl (wx.TextCtrl):
    def __init__ (self, *args, **kwargs):
        wx.TextCtrl.__init__(self, *args, **kwargs)
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def OnChar (self, e):
        key = e.GetKeyCode()
        if chr(key) in "1234567890":
            e.Skip()
        elif chr(key)=="-":
            v = wx.TextCtrl.GetValue(self)
            if v.count("-"):
                return wx.Bell()
            if not self.GetInsertionPoint():
                return e.Skip()
            wx.Bell()
        elif key in (wx.WXK_LEFT, wx.WXK_RIGHT, wx.WXK_DELETE, wx.WXK_BACK):
            e.Skip()
        elif chr(key)==".":
            if wx.TextCtrl.GetValue(self).count(".")==0:
                e.Skip()
            else:
                wx.Bell()
        else:
            wx.Bell()
