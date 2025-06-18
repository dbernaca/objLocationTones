# Part of the Object Location Tones settings package
# Intends to abstract serialization of the settings in order to support more file formats
# and even, possibly, loads from remote URLs
# Also, in the future, perhaps reflect the order of attribute creation within the settings file

from .objects import Holder
import json

__all__ = ["SDict"]

class SDict (dict):
    def dump (self, f):
        """
        Dumps the content of the SDict() into a settings file given by f.
        f --> A file-like object opened for writing.
        """
        json.dump(self, f, indent=4)

    def load (self, f):
        """
        Loads a settings file given by f into a SDict() instance.
        f --> A file-like object opened for reading
        It is a regular method instead of a class method so that existing
        SDict() can be edited before, but still updated from the file if necessary.
        Possible usage for this scenario is settings changes when updating.
        Returns self so that the load can be chained e.g.:
        d = SDict().load(f)
        """
        self.update(json.load(f))
        return self

    def to_instance (self):
        return Holder(self)

