# Part of the settings package
# Holds classes and functions that support settable attributes declaration

from logHandler import log
from inspect import currentframe as getframe, isclass
from .controls   import IntCtrl, FloatCtrl
from .exceptions import *
from gui.guiHelper import associateElements
import wx

class Attribute (object):
    """
    Attribute holder for settings purposes.
    Defines all important aspects of an attribute.
    When an attribute of an instance is set to an instance of the Attribute() class, it will be detected by
    the Settings() methods like load() and used to manage those.
    All such attributes will be included in settings and replaced with their real value.
    To define an Attribute() within your instance, use the Settable() factory function.
    """
    __slots__ = ("instance", "name", "type", "_value", "nickname", "default", "original", "args", "_firstset",
                 "__getitem__", "__setitem__", "__delitem__", "__contains__")
    def __init__ (self, instance, name, type, value, nickname, args):
        if instance is not Ellipsis:
            # If instance is Ellipsis, the __set_name__() is expected to set it, otherwise:
            object.__setattr__(self, "instance", instance)
        if name is not Ellipsis:
            # If name is not set, the __getattr__() is going to find it within the self.instance and set it.
            self.name = name
        # If None, then it is the same as the name (which may be undefined, i.e. Ellipsis),
        # and if Ellipsis, then __getattr__() will set it to name if called and not set in the midtime.
        # We set it only if it is defined
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
        object.__setattr__(self, "_firstset", True)

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
            if "callable" in self.args:
                parent.Bind(wx.EVT_CHECKBOX, self.args["callable"], ctrl)
            return ctrl
        if self.type==str:
            ctrl = wx.TextCtrl(parent, value=self.get())
            if "label" in self.args:
                label = wx.StaticText(parent, wx.ID_ANY, label=self.args["label"])
                return associateElements(label, ctrl)
            return ctrl
        if self.type==int:
            label = wx.StaticText(parent, wx.ID_ANY, label=self.args["label"])
            if "min" not in self.args and "max" not in self.args:
                return associateElements(label, IntCtrl(parent, value=str(self.get())))
            minval = self.args.get("min", 0)
            maxval = self.args.get("max", minval+100)
            label  = wx.StaticText(parent, wx.ID_ANY, label=self.args["label"])
            slider = wx.Slider(parent, wx.ID_ANY, minValue=minval, maxValue=maxval, value=self.get())
            return associateElements(label, slider)
        if self.type==float:
            label = wx.StaticText(parent, wx.ID_ANY, label=self.args["label"])
            if "min" not in self.args and "max" not in self.args:
                return associateElements(label, FloatCtrl(parent, value=str(self.get())))
            minval = self.args.get("min", 0)
            maxval = self.args.get("max", minval+100)
            label  = wx.StaticText(parent, wx.ID_ANY, label=self.args["label"])
            slider = wx.Slider(parent, wx.ID_ANY, minValue=minval, maxValue=maxval, value=int(round(self.get()*self.args.get("ratio", 1))))
            return associateElements(label, slider)

def Settable (value, nickname=None, *args, **kwargs):
    """
    This function is meant to be called within your instance's method or class
    when defining an attribute that will later be managed by the Settings() object.
    E.g.:
    >>> class a:
    >>>     b = Settable(1)
    >>>     def __init__ (self):
    >>>         self.something = Settable(5)
    >>>
    After you use one of the Settings()'s object methods on your instance, the attribute will be recognized as settable, and replaced
    with your defined value, or with the value loaded from the settings file.
    The function expects to be called from a method or directly from the class.
    Within methods, the "self", or, in case of classmethods, "cls" variables are expected,
    so keep the conventional argument names or Settable() will not work.
    Also, the class level Settable()s will later be treated as instance attributes,
    and class level values will not be affected.
    That is, the class level attribute declared Settable() object, can stay Attribute() object forever.
    """
    f = getframe().f_back
    if "__module__" in f.f_locals and "__qualname__" in f.f_locals:
        # Called within a class body
        obj = Ellipsis # Name and instance autodetect via descriptor protocol
    else:
        obj = f.f_locals.get("self", f.f_locals.get("cls"))
    args = dict(enumerate(args))
    args.update(kwargs)
    if obj is not None:
        return Attribute(obj, Ellipsis, type(value), value, nickname, args)
    raise SettingsError("Settable() must be called from within a class or a method")
