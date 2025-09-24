# Part of the Object Location Tones settings package
# Intends to abstract serialization of the settings in order to support more file formats
# and even, possibly, loads from remote URLs
# Also, in the future, perhaps reflect the order of attribute creation within the settings file
# Provides also the safe way to save the thing in atomic way

from .objects import Holder
from tempfile import mkstemp
from shutil import copyfileobj
from threading import Lock
import winKernel
import os
import json

__all__ = ["SDict", "SafeFile"]

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

class SafeFile:
    """
    Windows-only atomic file class with full read/write/append support.

    Features:
    - Atomic replace of the destination file upon successful close.
    - Handles modes: r, w, a, x, and all with '+' variants (r+, w+, a+, x+).
    - Copies existing file contents when necessary (r+, a, a+, etc.).
    - Ensures flush + fsync before atomic replace.
    - Uses MoveFileExW(REPLACE_EXISTING | WRITE_THROUGH) for durability (metadata is replaced along with data stream immediately).
    - It is thread-safe i.e. if a second SafeFile() instance is created referring to the same target file, the second instance will block until the first closes and moves the file

    After closing or exiting the context manager, the temporary file replaces the real target file.
    Inspired by fileUtils.FaultTolerantFile() function.
    This class allows for more flexibility though, and it is bug free.
    It implements complete file-like object, not only a context manager.
    Also, it takes care that, if non-existent file is opened for writing, a target file is created first,
    so that another process or thread are aware that the name is taken.
    What it does not do is to preserve file attrs or ACLs.
    If you change them on an existing file, they will revert to those of the temporary file after you call close() or exit the context.

    Possible usage:
    - Save config file so that if power is cutoff in the middle of the write the old config stays intact and thus, the possible file corruption does not impact your program execution
    - Save files, like big downloads, that if interrupted should not be presented to the user or used if incomplete

    You can change default behaviours using following keyword arguments:
    create_empty     --> Will create an empty target file if it doesn't exist, so that the name in FS is taken. Defaults to True, if False, the file will not be created which may be preferable in some situations
    delete_temporary --> Will delete the temporary file even if errors occurred during the handling of the file. Defaults to True. Setting it on False will leave the temp file for your inspection
    delete_target    --> Will delete the target file if it was created using create_empty so that the name is freed. Defaults to True. If create_empty is False, this argument influences nothing.
    Other constructor arguments and class behaviour is same as for the regular file object.

    TODO:
    - Add a resize using mmap for a created temp file so that disk space can be also reserved in advance, not only the target name.
      Good practice for large downloads. Need to know whether data will fit in advance and, also, prevent other processes from using the needed space in mid write.
    - Remove locks of closed files to preserve memory (not a priority)
    """
    locks = {} # Class attr: Keeps locks of safely opened files making the thing thread-safe per file
    def __init__ (self, name, mode="r", *args, **kwargs):
        self.mode = mode = mode.lower()
        self.name = name = os.path.abspath(name)
        self.create_empty = create_empty = kwargs.pop("create_empty", True)
        self.delete_temporary = kwargs.pop("delete_temporary", True)
        self.delete_target = kwargs.pop("delete_target", True)
        self.lock = lock = self.locks.setdefault(name, Lock())
        lock.acquire()
        writable = self.iswritable()
        if not writable:
            self._file = f = open(name, mode, *args, **kwargs)
            self._temp = None
            # Bind these as they are accessible after the file closes
            self.encoding = f.encoding
            self.newlines = f.newlines
            self.errors   = f.errors
            self.line_buffering = f.line_buffering
            self.write_through  = f.write_through
            return
        exists     = os.path.isfile(name)
        must_copy  = False
        must_exist = False
        if "a" in mode:
            must_copy = True
        elif "+" in mode:
            if "w" in mode or "x" in mode:
                must_copy = False  # w+ or x+ starts empty
            else:
                must_copy = True   # r+ requires original content
                must_exist = True
        if must_exist and not exists:
            raise FileNotFoundError(f"File {name!r} does not exist for mode {mode!r}")
        dirpath, filename = os.path.split(name)
        if create_empty and not exists:
            try:
                open(name, "x").close()
            except:
                lock.release()
                raise
        try:
            fd, tempfile = mkstemp(dir=dirpath, prefix=filename+".", suffix=".tmp")
            os.close(fd)
        except:
            lock.release()
            raise
        self._temp = tempfile
        # Copy original if needed
        if must_copy and exists:
            with open(name, "rb", buffering=0) as rf, open(tempfile, "wb", buffering=0) as wf:
                copyfileobj(rf, wf, length=1024**2)
        # Now open the temp file in requested mode
        self._file = f = open(tempfile, mode, *args, **kwargs)
        # Bind these as they are accessible after the file closes
        self.encoding = f.encoding
        self.newlines = f.newlines
        self.errors   = f.errors
        self.line_buffering = f.line_buffering
        self.write_through  = f.write_through

    iswritable = lambda self: any((flag in self.mode) for flag in ("w", "a", "x", "+"))

    class _dummyfunc:
        def __init__ (self, func):
            self.func = func
        def __call__ (self):
            raise ValueError("I/O operation on closed file.")
        def __repr__ (self):
            return f"<dummy function {self.func} at {hex(id(self))}"

    def __getattr__ (self, a):
        if a=="buffer" or a=="detach" or a=="reconfigure":
            # This is something you do not mess with in SafeFile()s so just report it as not here
            raise AttributeError("'SafeFile' object has no attribute '{a}'")
        f = self._file
        if f is None and (a=="tell" or a=="truncate" or a=="flush" or a=="isatty" or a.startswith("read") or a.startswith("write") or a.startswith("seek") or a=="__next__"):
            return self._dummyfunc(a)
        try:
            return getattr(f, a)
        except:
            raise AttributeError("'SafeFile' object has no attribute '{a}'")

    def __iter__ (self):
        f = self._file
        if f is None or f.closed:
            raise ValueError("I/O operation on closed file.")
        return iter(f)

    @property
    def closed (self):
        f = self._file
        return f is None or f.closed

    def close (self):
        f = self._file
        if f is None:
            return
        if not self.iswritable():
            f.close()
            self._file = None
            self.lock.release()
            return
        f.flush()
        os.fsync(f.fileno())
        f.close()
        self._file = None
        try:
            winKernel.moveFileEx(self._temp, self.name, winKernel.MOVEFILE_REPLACE_EXISTING | winKernel.MOVEFILE_WRITE_THROUGH)
            self.lock.release()
        except:
            if self.delete_temporary:
                try: os.unlink(self._temp)
                except: pass
            self.lock.release()
            raise

    # The underlying __enter__ method returns the wrong object
    # (self._file) so override it to return the wrapper
    def __enter__ (self):
        self._file.__enter__()
        return self

    # Need to trap __exit__ as well to ensure the temporary file gets
    # moved when used in a with statement
    def __exit__ (self, exc, value, tb):
        f = self._file
        if not self.iswritable():
            result = f.__exit__(exc, value, tb)
            self._file = None
            self.lock.release()
            return result
        if exc:
            result = f.__exit__(exc, value, tb)
            self._file = None
            if self.delete_temporary:
                try: os.unlink(self._temp)
                except: pass
            self.lock.release()
            return result
        f.flush()
        os.fsync(f.fileno())
        f.close()
        self._file = None
        try:
            winKernel.moveFileEx(self._temp, self.name, winKernel.MOVEFILE_REPLACE_EXISTING | winKernel.MOVEFILE_WRITE_THROUGH)
            self.lock.release()
        except:
            if self.delete_temporary:
                try: os.unlink(self._temp)
                except: pass
            self.lock.release()
            raise

    def __repr__ (self):
        where = self._temp if self._temp else self.name
        state = ("Opened", "Closed")[self.closed]
        return f"<{state} SafeFile(target={self.name!r}, mode={self.mode!r}, current={where!r}) object at {hex(id(self))}>"
