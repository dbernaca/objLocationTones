from gui.guiHelper import BoxSizerHelper
try:
    from gui.settingsDialogs import SettingsPanel
except:
    from gui import SettingsPanel

from globalPlugins.objloc.UIStrings import SET_CATEGORY
from .objects import Attribute

import weakref
import gui
import wx

def isSettableCtrl (obj):
    return hasattr(obj, "GetValue") or hasattr(obj, "SetStringSelection")

def getCtrl (obj):
    if not isSettableCtrl(obj):
        for x in obj.GetChildren():
            if isSettableCtrl(x.Window):
                obj = x.Window
                break
    return obj

def getValue (attr, obj):
    obj = getCtrl(obj)
    value = obj.GetStringSelection() if hasattr(obj, "SetStringSelection") else obj.GetValue()
    value = attr.type(value)
    if "ratio" in attr.args:
        value /= attr.args["ratio"]
    if "validator" in attr.args:
        value = attr.args["validator"](attr, value)
    return value

def setValue (obj, value):
    obj = getCtrl(obj)
    if "ratio" in attr.args:
        value *= attr.args["ratio"]
    if isinstance(obj, wx.TextCtrl):
        value = str(value)
    elif hasattr(obj, "SetStringSelection"):
        if isinstance(value, int):
            obj.SetSelection(value)
        elif isinstance(value, str):
            obj.SetStringSelection(value)
        else:
            obj.Set(value)
        return
    obj.SetValue(value)

class Panel (SettingsPanel):
    title       = SET_CATEGORY
    currentset  = lambda: None # Current settings instance to use stored as a weakref
    currentinst = lambda: None # Target instance on which the settings will be applied

    @classmethod
    def setActiveSettings (cls, settings_obj, target_instance):
        cls.currentset  = weakref.ref(settings_obj)
        cls.currentinst = weakref.ref(target_instance)

    def makeSettings (self, settingsSizer):
        self.controls = ctrls = {}
        settings = self.currentset()
        inst = self.currentinst()
        helper = BoxSizerHelper(self, sizer=settingsSizer)
        for attr in sorted(settings.attributes, key=(lambda x: x.args.get("ordinal", 0))):
            if not attr.belongs_to(inst):
                continue
            if "label" not in attr.args:
                continue
            item = attr.create_gui_control(self)
            helper.addItem(item)
            ctrls[attr] = item

    def onSave (self):
        try:
            settings = self.currentset()
            inst = self.currentinst()
            for attr, ctrl in self.controls.items():
                try:
                    attr.value = getValue(attr, ctrl)
                except:
                    print(attr.name)
                    raise
                attr.set()
            self.controls.clear()
            del self.controls
            settings.save(inst)
        except Exception as e:
            print(e)

def SetPanel (settings_obj, target_instance):
    Panel.setActiveSettings(settings_obj, target_instance)
    categoryClasses = gui.settingsDialogs.NVDASettingsDialog.categoryClasses
    if Panel not in categoryClasses:
        categoryClasses.append(Panel)

def RemovePanel ():
    categoryClasses = gui.settingsDialogs.NVDASettingsDialog.categoryClasses
    try:
        categoryClasses.remove(Panel)
    except ValueError:
        pass
