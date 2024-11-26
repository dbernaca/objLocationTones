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

    def map_attrs (self, instance):
        """
        Populates the attributes set() from the instance and
        puts real values in place of Attribute() objects.
        You may wish to call this method manually in cases
        where load() or save() has already been called, but you
        defined new Settable()s afterwards, or you wish to call
        the update() method without loading data from the file.
        """
        for attr in dir(instance):
            obj = getattr(instance, attr)
            if isinstance(obj, Attribute):
                if obj.is_class_attr():
                    obj = obj.copy()
                    obj.flip_allegiance(instance)
                self.attributes.add(obj)
                obj.set()

    def load (self, instance):
        """
        Loads the settings from the json file to the instance's attributes.
        If the file is not there, tries to create one with saved default settings, from the instance.
        When loading, if the attribute is not present in the file, it will be skipped with the logged warning.
        The value will be set to default one.
        If an attribute has a wrong type, the warning will be posted to the log, and loading continued with other attributes.
        The value will be set to the default one.
        """
        if not os.path.isfile(self.path):
            # If there is no settings file,
            # make the attribute map and save defaults to file immediately
            self.save(instance, force=True)
            # No point loading back from file
            self.lversion = self.version
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
        self.map_attrs(instance)
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
        self.map_attrs(instance)
        # Build the JSON dict
        d = {"version": self.version} # Save the protocol version, so we may adapt to older settings if it changes in the future
        changed = []
        for attr in self.attributes:
            if not attr.belongs_to(instance):
                # Do not change settings from other instances
                # but make sure they are written to file
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
            # If writing to file is successful, make sure new original values
            # now are the ones saved, just like the file is just loaded
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

    def generate_instance (self):
        """
        Returns a holder instance containing all attributes from the settings file,
        except for the 'version' attribute. Attribute names are actually nicknames from
        the settings file, and all Python incompatible names will just be skipped.
        The instance can be used for settings transition, or temporary save etc.
        They can be loaded from the instance to another instance via update() method.
        """
        if not os.path.isfile(self.path):
            raise SettingsError("No settings file at '%s'" % self.path)
        try:
            f = open(self.path)
        except Exception as e:
            raise SettingsError("Opening settings file failed because of "+str(e))
        try:
            d = json.load(f)
        except Exception as e:
            raise SettingsError("Loading of the settings from file failed because of "+str(e))
        class holder:
            pass
        obj = holder()
        d.pop("version", 123)
        for key, value in d.items():
            attr = Attribute(obj, key, type(value), value, key, {})
            try:
                setattr(obj, key, attr)
            except:
                log.warning("Invalid name: %s, skipping...." % repr(key))
        return obj

    def update (self, instance):
        """
        Updates values from another instance to their instances.
        All registered Attributes() will be tried,
        first by name, then by nickname, and if found in 'instance',
        their value will be updated to the one from the 'instance'.
        Can be used to update current settings from raw settings load by generate_instance() method.
        Do not forget to call load(), save() or map_attrs() on the instance(s) you wish to update
        before the update() method, so that the set() attributes is populated.
        Type mismatches and similar problems with value will be logged and the attribute skipped.
        """
        for attr in self.attributes:
            try:
                newval = getattr(instance, attr.name, getattr(instance, attr.nickname))
            except:
                log.warning("No attribute '%s', nor '%s', skipping...." % (attr.name, attr.nickname))
                continue
            newval = newval.value if isinstance(newval, Attribute) else newval
            try:
                attr.value = newval
            except SettingsError as e:
                log.warning("%s for attribute '%s', skipping..." % (str(e), attr.name))
                continue
            try:
                attr.set()
            except SettingsError:
                raise
            except Exception as e:
                raise SettingsError("Unable to set the attribute '%s' to value %s because of %s" % (attr.name, repr(value), str(e)))
