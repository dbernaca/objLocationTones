# This package belongs to Object Location Tones NVDA add-on
# Its purpose is to manage all aspects of settings for the add-on
# From saving them to disk, to providing GUI

import os
import json
from logHandler import log
from inspect import currentframe as getframe, ismethod, isclass

__all__ = ["SettingsError", "Attribute", "Settable", "Settings"]

class SettingsError (Exception):
    """Raised when anything goes wrong with settings management."""

class Attribute (object):
    """
    Attribute holder for settings purposes.
    Defines all important aspects of an attribute.
    When an attribute of an instance is set to an instance of the Attribute() class, it will be detected by
    the Settings() methods like load() and used to manage those.
    All such attributes will be included in settings and replaced with their real value.
    To define an Attribute() within your instance, use the Settable() factory function.
    """
    __slots__ = ("instance", "_name", "type", "_value", "_nickname", "default")
    def __init__ (self, instance, name, type, value, nickname):
        self.instance  = instance
        self._name     = name
        self._nickname = nickname if nickname else name
        self.type      = type
        self._value    = value
        self.default   = self.value

    @staticmethod
    def from_instance (instance, attr):
        """
        Creates a new Attribute() instance from the given attribute of the given instance.
        If the attribute of the instance already is an Attribute() object
        then a copy of the object will be returned instead.
        """
        value = getattr(instance, attr)
        if isinstance(value, Attribute):
            return Attribute(instance, attr, value.type, value.value, value.nickname)
        return Attribute(instance, attr, type(value), value, attr)

    def to_instance (self, instance):
        """
        Set this Attribute()'s value to the given instance.
        If the instance does not have the attribute declared, it will be created but only if the name is specified, if it is not an error will occur.
        """
        setattr(instance, self.name, self.value)

    def _get_name (self):
        """
        An internal name getter method.
        If the name is still undefined then it extracts and sets it using backward introspection.
        Never call it directly, use the name property instead.
        """
        if self._name is not Ellipsis:
            return self._name
        this = id(self)
        name = None
        # Get out of the property() instance
        f = getframe().f_back.f_back.f_back
        while name is None and f:
            inst = f.f_locals.get("self", f.f_locals.get("cls"))
            while not inst and f:
                f = f.f_back
                inst = f.f_locals.get("self", f.f_locals.get("cls"))
            if not inst:
                raise SettingsError("Cannot find the attribute name")
            for attr in dir(inst):
                value = getattr(inst, attr)
                if id(value)==this:
                    name = attr
                    break
            if name is None:
                f = f.f_back
        if name is None:
            raise SettingsError("Cannot find the attribute name")
        self._name = name
        return name

    def _set_name (self, name):
        """
        An internal name setter method.
        Sets the name to the given value.
        Never call it directly, use the name property() instead.
        """
        if not isinstance(name, str):
            raise SettingsError("The name must be a string")
        self._name = name
    name = property(_get_name, _set_name)

    def _get_nickname (self):
        """
        An internal nickname getter method.
        If the nickname is still undefined then it is set to self.name.
        Never call it directly, use the name property instead.
        """
        if self._nickname is not Ellipsis:
            return self._nickname
        name = self.name
        self._nickname = name
        return name

    def _set_nickname (self, nickname):
        """
        An internal nickname setter method.
        Sets the nickname to the given value.
        Never call it directly, use the nickname property() instead.
        """
        if not isinstance(nickname, str):
            raise SettingsError("The nickname must be a string")
        self._nickname = nickname
    nickname = property(_get_nickname, _set_nickname)

    def set (self):
        """
        Assigns the value to the instance's attribute.
        """
        setattr(self.instance, self.name, self.value)

    def get (self):
        """
        Returns the value of an attribute.
        The value from the instance if real, the valu from the Attribute() if still the Attribute() object
        and, if an attribute does not exist in the instance, tries to create it  returning the Attribute()'s value.
        This will also update the Attribute()'s value to the instance's value.
        To get the original, use the default attribute.
        """
        try:
            value = getattr(self.instance, self.name)
            value = value.value if isinstance(value, Attribute) else value
            self.value = value
        except AttributeError:
            self.set()
            value = self._value
        return value

    # Use property() to define type checking which is important when loading from file.
    # If the file was manually altered and wrong type was used, we must avoid problems.
    def set_value (self, value):
        if not isinstance(value, self.type):
            raise SettingsError("Wrong type for attribute %s. '%s' given, '%s' expected." % (self.name, value.__class__.__name__, self.type.__name__))
        self._value = value

    def get_value (self):
        if not isinstance(self._value, self.type):
            raise SettingsError("Wrong type for attribute %s. '%s' given, '%s' expected." % (self.name, self._value.__class__.__name__, self.type.__name__))
        return self._value
    value = property(get_value, set_value)

    def __hash__ (self):
        return self.name.__hash__()

def Settable (value, nickname=None):
    """
    This function is meant to be called within your instance's method,
    when defining an attribute that will later be managed by the Settings() object.
    E.g.:
    >>> self.something = Settable(5)
    After you use a Settings() method on your instance, the attribute will be recognized as settable, and replaced
    with your defined value, or with the value loaded from the settings file.
    The function expects to be called from a method or directly from the class.
    """
    f = getframe().f_back
    if "__module__" in f.f_locals and "__qualname__" in f.f_locals:
        # Called within a class body
        obj = f.f_back.f_locals[f.f_locals["__qualname__"]]
    else:
        obj = f.f_locals.get("self", f.f_locals.get("cls"))
    if obj:
        return Attribute(obj, Ellipsis, type(value), value, nickname)
    raise SettingsError("Settable() must be called from within a class or a method")

class Settings:
    path    = None # A settings file
    lastset = {} # To check whether settings were changed and in need of saving
    version = 1 # Version of the settings protocol

    def __init__ (self, path=None):
        self.path   = path or os.path.join(os.path.abspath(os.path.dirname(__file__)), "settings.json")
        self.attributes = set()

    def load (self, instance):
        """
        Loads the settings from the json file to the instance's attributes.
        If the file is not there, tries to create one with default settings, from the instance, saved.
        When loading, if the attribute is not present, it will be skipped with the logged warning.
        The value will be set to default one.
        If an attribute has a wrong type, the warning will be posted to the log, and loading continued with other attributes.
        The value will be set to the default one.
        """
        if not os.path.isfile(self.path):
            self.save(instance, force=True)
            return
        try:
            f = open(self.path)
        except Exception as e:
            raise SettingsError("Opening settings file failed because of "+str(e))
        try:
            d = json.load(f)
        except Exception as e:
            raise SettingsError("Loading of the settings from file failed because of "+str(e))
        # Update the set() attributes
        for attr in dir(instance):
            obj = getattr(instance, attr)
            if isinstance(obj, Attribute):
                self.attributes.add(obj)
                obj.set()
        ld = {} # Keep local record to avoid saving settings if it isn't necessary
        for attr in self.attributes:
            if attr.instance!=instance:
                # If settings is shared between multiple instances, skip attributes which do not belong
                continue
            try:
                value = d[attr.nickname]
                attr.value = value
            except SettingsError as e:
                log.warning(str(e))
                continue
            except KeyError:
                log.warning("Attribute '%s' requested but not found in the file." % attr.nickname)
                continue
            try:
                attr.set()
                ld[attr.name] = attr.value
            except SettingsError:
                raise
            except Exception as e:
                raise SettingsError("Unable to set the attribute '%s' to value %s because of %s" % (attr.name, repr(value), str(e)))
        ld["version"] = d.get("version", self.version)
        self.lastset = ld

    def save (self, instance, force=False):
        """
        Saves settings to the file from attributes of the given instance.
        The save will not occur if there were no changes in the settings. The save can the forced though using the force=True.
        Unaccessible instance attributes will be skipped.
        If there is a type mismatch, a worning will be posted to the log, the attribute skipped and the process continued.
        """
        # Update the attributes set() in case new attributes were registered for saving
        for attr in dir(instance):
            obj = getattr(instance, attr)
            if isinstance(obj, Attribute):
                self.attributes.add(obj)
                obj.set()
        # Build the JSON dict
        d = {"version": self.version} # Save the protocol version, so we may adapt to older settings if it changes in the future
        for attr in self.attributes:
            if attr.instance!=instance:
                # Do not change settings from other instances
                continue
            try:
                value = attr.get()
            except SettingsError as e:
                log.warning(str(e))
                continue
            d[attr.nickname] = value
        if not force:
            if self.lastset==d:
                return
        try:
            f = open(self.path, "w")
            json.dump(d, f, indent=4)
            f.close()
        except Exception as e:
            raise SettingsError("Unable to save settings because of %s"+str(e))
        self.lastset = d