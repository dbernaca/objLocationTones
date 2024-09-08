# This package belongs to Object Location Tones NVDA add-on
# Its purpose is to manage all aspects of settings for the add-on
# From saving them to disk, to providing GUI

import os
import json
from logHandler import log
from .objects import *
from .exceptions import *
from .panel import SetPanel, RemovePanel

__all__ = ["SettingsError", "Attribute", "Settable", "Settings", "SetPanel", "RemovePanel"]

class Settings:
    path     = None # A settings file
    version  = 1    # Version of the settings protocol
    lversion = None # Version from the loaded file
    def __init__ (self, path=None):
        self.path       = path or os.path.join(os.path.abspath(os.path.dirname(__file__)), "settings.json")
        self.attributes = set()

    def load (self, instance):
        """
        Loads the settings from the json file to the instance's attributes.
        If the file is not there, tries to create one with default settings, from the instance, saved.
        When loading, if the attribute is not present in the file, it will be skipped with the logged warning.
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
                if obj.is_class_attr():
                    obj = obj.copy()
                    obj.flip_allegiance(instance)
                self.attributes.add(obj)
                obj.set()
        for attr in self.attributes:
            if not attr.belongs_to(instance):
                # If settings is shared between multiple instances, skip attributes which do not belong to this one
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
            except SettingsError:
                raise
            except Exception as e:
                raise SettingsError("Unable to set the attribute '%s' to value %s because of %s" % (attr.name, repr(value), str(e)))
        self.lversion = d.get("version", self.version)

    def save (self, instance, force=False):
        """
        Saves settings to the file from attributes of the given instance.
        The save will not occur if there were no changes in the settings. The save can the forced though using the force=True.
        Inaccessible instance attributes will be skipped.
        If there is a type mismatch, a worning will be posted to the log, the attribute skipped and the process continued.
        """
        # Update the attributes set() in case new attributes were registered for saving
        for attr in dir(instance):
            obj = getattr(instance, attr)
            if isinstance(obj, Attribute):
                if obj.is_class_attr():
                    obj = obj.copy()
                    obj.flip_allegiance(instance)
                self.attributes.add(obj)
                obj.set()
        # Build the JSON dict
        d = {"version": self.version} # Save the protocol version, so we may adapt to older settings if it changes in the future
        changed = []
        for attr in self.attributes:
            if not attr.belongs_to(instance):
                # Do not change settings from other instances
                d[attr.nickname] = attr.original
                continue
            try:
                value = attr.get()
            except SettingsError as e:
                log.warning(str(e))
                continue
            d[attr.nickname] = value
            if attr.has_changed():
                changed.append(attr)
        if not force:
            if not changed:
                return
        try:
            f = open(self.path, "w")
            json.dump(d, f, indent=4)
            f.close()
            for attr in changed:
                attr.seal()
        except Exception as e:
            raise SettingsError("Unable to save settings because of %s"+str(e))

    def restore_defaults (self):
        for attr in self.attributes:
            attr.value = attr.default
            attr.set()

    def restore_original (self):
        for attr in self.attributes:
            attr.value = attr.original
            attr.set()

    def __getitem__ (self, i):
        for attr in self.attributes:
            if attr.name==i:
                return attr
        raise KeyError("'%s' not found" % i)

    def __contains__ (self, i):
        return (i in (attr.name for attr in self.attributes))
