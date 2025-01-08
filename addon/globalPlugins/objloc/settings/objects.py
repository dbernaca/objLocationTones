# Part of the settings package
# Holds classes and functions that support settable attributes declaration

from logHandler    import log
from inspect       import isclass
from .controls     import IntCtrl, FloatCtrl, SliderCtrl
from .exceptions   import *
from gui.guiHelper import associateElements
import wx

class Flag (object):
    value = True
    def __init__ (self, value):
        self.value = value

    def __bool__ (self):
        return self.value
    __nonzero__ = __bool__

    def toggle (self):
        self.value = not self.value

    def set (self):
        self.value = True

    def clear (self):
        self.value = False

    def __repr__ (self):
        return repr(self.value)

class IdGenerator (object):
    __slots__ = ("ids",)
    def __init__ (self):
        self.ids = {}

    def __call__ (self, instance):
        clsid = id(instance) if isclass(instance) else id(instance.__class__)
        self.ids[clsid] = newid = self.ids.get(clsid, -1)+1
        return newid

    def last (self, instance):
        clsid = id(instance) if isclass(instance) else id(instance.__class__)
        return self.ids.get(clsid, 0)

    def len (self, instance):
        clsid = id(instance) if isclass(instance) else id(instance.__class__)
        return self.ids.get(clsid, -1)+1

    def reset (self, instance):
        clsid = id(instance) if isclass(instance) else id(instance.__class__)
        try:
            del self.ids[clsid]
        except KeyError:
            pass

GenerateId = IdGenerator()

class Attribute (object):
    """
    Attribute holder for settings purposes.
    Defines all important aspects of an attribute.
    When an attribute of an instance is set to an instance of the Attribute() class, it will be detected by
    the Settings() methods like load() and used to manage those.
    All such attributes will be included in settings and replaced with their real value.
    To define an Attribute() within your instance, use the Settable() factory function.
    """
    __slots__ = ("instance", "name", "type", "_value", "nickname", "default", "original", "args", "_firstset", "id",
                 "skip", "save", "show", "ctrlId", "feedback",
                 "__getitem__", "__setitem__", "__delitem__", "__contains__")
    def __init__ (self, instance, name, type, value, nickname, args):
        if instance is not Ellipsis:
            # If instance is Ellipsis, the __set_name__() is expected to set it, otherwise:
            object.__setattr__(self, "instance", instance)
            object.__setattr__(self, "id", GenerateId(instance))
        if name is not Ellipsis:
            # If name is not set, the __getattr__() is going to find it within the self.instance and set it.
            self.name = name
        # If nickname is None, then it is the same as the name (which may be undefined, i.e. Ellipsis),
        # and if Ellipsis, then __getattr__() will set it to name if called and not set in the midtime.
        # We set it only if it is defined in args or if it is not, only if name is defined
        if nickname:
            self.nickname = nickname
        elif name is not Ellipsis:
            self.nickname = name
        object.__setattr__(self, "type", type)
        object.__setattr__(self, "_value", value)
        object.__setattr__(self, "default", self.value) # Use self.value here to check for type mismatch
        object.__setattr__(self, "original", value)
        object.__setattr__(self, "args", (args or {}))
        object.__setattr__(self, "__getitem__", self.args.__getitem__)
        object.__setattr__(self, "__setitem__", self.args.__setitem__)
        object.__setattr__(self, "__delitem__", self.args.__delitem__)
        object.__setattr__(self, "__contains__", self.args.__contains__)
        object.__setattr__(self, "ctrlId", None)
        object.__setattr__(self, "feedback", args.get("feedback", None))
        object.__setattr__(self, "_firstset", True)
        object.__setattr__(self, "skip", args.get("skip", False))
        object.__setattr__(self, "save", args.get("save", True))
        object.__setattr__(self, "show", args.get("show", True))

    @staticmethod
    def from_instance (instance, attr):
        """
        Creates a new Attribute() object from the given attribute of the given instance.
        If the attribute of the instance already is an Attribute() object
        then a copy of the object will be returned instead.
        """
        value = getattr(instance, attr)
        if isinstance(value, Attribute):
            return Attribute(instance, attr, value.type, value.value, value.nickname, value.args.copy())
        return Attribute(instance, attr, type(value), value, attr, None)

    def to_instance (self, instance):
        """
        Set this Attribute()'s value to the given instance.
        If the instance does not have the attribute declared, it will be created but only if the name is specified, if it is not an error will occur.
        The method sets the real value from self.value to the instance, not the Attribute() object itself.
        """
        setattr(instance, self.name, self.value)

    def copy (self):
        return Attribute(self.instance, self.name, self.type, self.value, self.nickname, self.args.copy())

    def __getattr__ (self, a):
        if a=="name":
            this = id(self)
            name = None
            inst = self.instance
            for attr in dir(inst):
                value = getattr(inst, attr)
                if id(value)==this:
                    name = attr
                    break
            if name is None:
                raise SettingsError("Cannot find the attribute name")
            object.__setattr__(self, "name", name)
            return name
        elif a=="nickname":
            name = self.name
            object.__setattr__(self, "nickname", name)
            return name
        elif a=="value":
            value = self._value
            if not isinstance(value, self.type):
                raise SettingsError("Wrong type for attribute %s. '%s' given, '%s' expected." % (self.name, value.__class__.__name__, self.type.__name__))
            return value
        raise AttributeError("No attribute named "+repr(a))

    def __setattr__ (self, a, v):
        if a=="name":
            if not isinstance(v, str):
                raise SettingsError("The name must be a string")
            object.__setattr__(self, "name", v)
        elif a=="nickname":
            if not isinstance(v, str):
                raise SettingsError("The nickname must be a string")
            object.__setattr__(self, "nickname", v)
        elif a=="value":
            if not isinstance(v, self.type):
                raise SettingsError("Wrong type for attribute %s. '%s' given, '%s' expected." % (self.name, v.__class__.__name__, self.type.__name__))
            object.__setattr__(self, "_value", v)
            if self._firstset:
                object.__setattr__(self, "original", v)
                object.__setattr__(self, "_firstset", False)
        else:
            raise AttributeError("The Attribute() object only allows certain attributes to be set")

    def set (self):
        """
        Assigns the Attribute()'s value to the instance's attribute.
        """
        setattr(self.instance, self.name, self.value)

    def reset (self):
        """
        Assigns the Attribute() object to the instance's attribute.
        """
        setattr(self.instance, self.name, self)

    def get (self):
        """
        Returns the value of an attribute.
        The value from the instance if real, the valu from the Attribute() if still the Attribute() object
        and, if an attribute does not exist in the instance, tries to create it  returning the Attribute()'s value.
        This will also update the Attribute()'s value to the instance's value.
        To get the original, use the default attribute.
        When an attribute is created, the real value will be assigned to it, not the Attribute() object itself.
        When the attribute is still the Attribute() object, it will not be cast to real value, but stay that way.
        """
        try:
            value = getattr(self.instance, self.name)
            value = value.value if isinstance(value, Attribute) else value
            self.value = value
        except AttributeError:
            self.set()
            value = self.value
        return value

    def __hash__ (self):
        return self.name.__hash__()

    def __set_name__ (self, owner, name):
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "instance", owner)
        object.__setattr__(self, "id", GenerateId(owner))

    def getargs (self):
        args   = [value for arg, value in sorted((item for item in self.args.items() if isinstance(item[0], int)), key=lambda x: x[0])]
        kwargs = dict((arg, value) for arg, value in self.args if isinstance(arg, str))
        return args, kwargs
        
    def status (self):
        if self._firstset:
            return "set to default"
        if self._value==self.original and self._value==self.default:
            return "sealed to default"
        if self._value==self.original:
            return "sealed to value"
        return "changed"

    def has_changed (self):
        return self._value!=self.original

    def seal (self):
        object.__setattr__(self, "original", self._value)

    def belongs_to (self, instance):
        return isinstance(instance, self.instance) if isclass(self.instance) else id(instance)==id(self.instance)

    def is_class_attr (self):
        return isclass(self.instance)

    def flip_allegiance (self, instance):
        object.__setattr__(self, "instance", instance)

    def create_gui_control (self, parent):
        if self.type==bool:
            ctrl = wx.CheckBox(parent, label=self.args["label"])
            ctrl.SetValue(self.get())
            if "reactor" in self.args:
                parent.Bind(wx.EVT_CHECKBOX, self.args["reactor"], ctrl)
            object.__setattr__(self, "ctrlId", ctrl.GetId())
            parent.Bind(wx.EVT_WINDOW_DESTROY, (lambda e: object.__setattr__(self, "ctrlId", None)), ctrl)
            return ctrl
        if "choices" in self.args:
            label = wx.StaticText(parent, wx.ID_ANY, label=self.args["label"])
            if self.type==tuple:
                ctrl = wx.Choice(parent, wx.ID_ANY, choices=self.args["choices"])
            else:
                ctrl = wx.ListBox(parent, wx.ID_ANY, choices=self.args["choices"], style=wx.LB_SINGLE)
            if self.args["choices"]:
                value = self.get()
                if self.type==int:
                    ctrl.SetSelection(value if 0<=value<len(self.args["choices"]) else 0)
                elif value in self.args["choices"]:
                    ctrl.SetStringSelection(value)
                else:
                    ctrl.SetSelection(0)
            if "reactor" in self.args:
                parent.Bind((wx.EVT_CHOICE if self.type==tuple else wx.EVT_LISTBOX), self.args["reactor"], ctrl)
            object.__setattr__(self, "ctrlId", ctrl.GetId())
            parent.Bind(wx.EVT_WINDOW_DESTROY, (lambda e: object.__setattr__(self, "ctrlId", None)), ctrl)
            return associateElements(label, ctrl)
        if self.type==str:
            ctrl = wx.TextCtrl(parent, value=self.get())
            object.__setattr__(self, "ctrlId", ctrl.GetId())
            parent.Bind(wx.EVT_WINDOW_DESTROY, (lambda e: object.__setattr__(self, "ctrlId", None)), ctrl)
            if "label" in self.args:
                label = wx.StaticText(parent, wx.ID_ANY, label=self.args["label"])
                return associateElements(label, ctrl)
            return ctrl
        if self.type==int:
            label = wx.StaticText(parent, wx.ID_ANY, label=self.args["label"])
            if "min" not in self.args and "max" not in self.args:
                ctrl = IntCtrl(parent, value=str(self.get()))
                object.__setattr__(self, "ctrlId", ctrl.GetId())
                parent.Bind(wx.EVT_WINDOW_DESTROY, (lambda e: object.__setattr__(self, "ctrlId", None)), ctrl)
                return associateElements(label, ctrl)
            minval = self.args.get("min", 0)
            maxval = self.args.get("max", minval+100)
            slider = SliderCtrl(parent, wx.ID_ANY, minValue=minval, maxValue=maxval, value=self.get())
            object.__setattr__(self, "ctrlId", slider.GetId())
            parent.Bind(wx.EVT_WINDOW_DESTROY, (lambda e: object.__setattr__(self, "ctrlId", None)), slider)
            return associateElements(label, slider)
        if self.type==float:
            label = wx.StaticText(parent, wx.ID_ANY, label=self.args["label"])
            if "min" not in self.args and "max" not in self.args:
                ctrl = FloatCtrl(parent, value=str(self.get()))
                object.__setattr__(self, "ctrlId", ctrl.GetId())
                parent.Bind(wx.EVT_WINDOW_DESTROY, (lambda e: object.__setattr__(self, "ctrlId", None)), ctrl)
                return associateElements(label, ctrl)
            minval = self.args.get("min", 0)
            maxval = self.args.get("max", minval+100)
            slider = SliderCtrl(parent, wx.ID_ANY, minValue=minval, maxValue=maxval, value=int(round(self.get()*self.args.get("ratio", 1))))
            object.__setattr__(self, "ctrlId", slider.GetId())
            parent.Bind(wx.EVT_WINDOW_DESTROY, (lambda e: object.__setattr__(self, "ctrlId", None)), slider)
            return associateElements(label, slider)
        if self.type==type(Ellipsis):
            ctrl = wx.Button(parent, label=self.args["label"])
            parent.Bind(wx.EVT_BUTTON, self.args["reactor"], ctrl)
            object.__setattr__(self, "ctrlId", ctrl.GetId())
            parent.Bind(wx.EVT_WINDOW_DESTROY, (lambda e: object.__setattr__(self, "ctrlId", None)), ctrl)
            return ctrl

    def get_gui_control (self, parent=None):
        ctrlId = self.ctrlId
        if ctrlId is None:
            if parent:
                return self.create_gui_control(parent)
            return
        return wx.FindWindowById(ctrlId, parent)

    def has_gui_control (self):
        return self.ctrlId!=None
