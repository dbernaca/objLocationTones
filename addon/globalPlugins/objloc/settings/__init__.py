# This package belongs to Object Location Tones NVDA add-on
# Its purpose is to manage all aspects of settings for the add-on
# From saving them to disk, to providing GUI

import os
import json

__all__ = ["SettingsError", "Settings"]

# Attributes to load and save
ATTRIBUTES = {
    "active": bool,
    "duration": int,
    "volume": float,
    "stereoSwap": bool,
    "tolerance": int,
    "timeout": float,
    "caret": bool}

class SettingsError (Exception):
    """Raised when anything goes wrong with settings management."""

class Settings:
    path    = None # A settings file
    lastset = {} # To check whether settings were changed and in need of saving
    version = 1 # Version of the settings protocol

    def __init__ (self, path=None):
        self.path   = path or os.path.join(os.path.abspath(os.path.dirname(__file__)), "settings.json")

    def load (self, instance):
        """
        Loads the settings from the json file to the instance's attributes.
        If the file is not there, tries to create one with default settings, from the instance, saved.
        When loading, if the attribute is not present, it will be skipped.
        If an attribute has a wrong type, the warning will be posted to the log, and loading continued with other attributes.
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
        ld = {} # Keep local record to avoid saving if it isn't necessary
        for attr, type in ATTRIBUTES.items():
            try:
                value = d[attr]
            except KeyError:
                pass
            if not isinstance(value, type):
                print("Warning: Wrong type for attribute %s. '%s' given, '%s' expected." % (attr, value.__class__.__name__, type.__name__))
                continue
            try:
                setattr(instance, attr, value)
                ld[attr] = value
            except Exception as e:
                raise SettingsError("Unable to set the attribute '%s' to value %s because of %s" % (attr, repr(value), str(e)))
        ld["version"] = d.get("version", self.version)
        self.lastset = ld

    def save (self, instance, force=False):
        """
        Saves settings to the file from attributes of the given instance.
        If force is True (defaults to False) the save will not occur unles self.changed is True.
        Unaccessible instance attributes will be skipped.
        If there is a type mismatch, a worning will be posted to the log, the attribute skipped and the process continued.
        """
        # Build the JSON dict
        d = {"version": self.version} # Save the protocol version, so we may adapt to older settings if it changes in the future
        for attr, type in ATTRIBUTES.items():
            try:
                value = getattr(instance, attr)
            except AttributeError:
                pass
            if not isinstance(value, type):
                print("Warning: Wrong type for attribute %s. '%s' given, '%s' expected." % (attr, value.__class__.__name__, type.__name__))
                continue
            d[attr] = value
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