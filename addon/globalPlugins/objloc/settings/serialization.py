# Part of the Object Location Tones settings package
# Intends to abstract serialization of the settings in order to support more file formats
# and even, possibly, loads from remote URLs
# Also, in the future, perhaps reflect the order of attribute creation within the settings file
# Provides also a safe way to save the serialized data in an atomic way

from .objects import Holder
from tempfile import mkstemp
from stat import S_ISREG
from glob import glob
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
    Windows-only atomic file writer with read/write/append support.
    Inspired by NVDA's fileUtils.FaultTolerantFile() function.
    This class allows for more flexibility though, and fixes bugs that are present there.
    It implements a file-like object, not only a context manager.

    Copyright (C) 2026 by Dalen Bernaca under GPL

    Overview
    --------
    SafeFile writes to a temporary file in the same directory as the target
    and, on successful close or context manager exit, atomically replaces the
    target with the temporary file. If an error occurs before the replacement
    step, the original target is left unchanged and the temporary file is
    cleaned up (unless configured otherwise).
    When opened in read-only mode, SafeFile behaves like a thin wrapper
    around a regular file object and does not create or replace any temporary files.

    This class is intended for scenarios where partially written files must
    never be observed as the "real" file, such as configuration files or
    larger downloads that should only appear once fully written.

    Semantics
    ---------
    * Supported modes: 'r', 'w', 'a', 'x' and all their '+' variants
      ('r+', 'w+', 'a+', 'x+'), with text/binary variants as accepted by
      built-in open().
    * Read-only modes ('r', 'rb') open the target file directly and do not use
      a temporary file or perform any replacement.
    * Writable modes ('w', 'w+', 'a', 'a+', 'x', 'x+', and their binary
      variants) always write to a temporary file and, on successful close or
      context exit, replace the target file with that temporary file.
    * For modes that conceptually start from existing content ('r+', 'a',
      'a+'), SafeFile first copies the current contents of the target into
      the temporary file before exposing the file object to the caller.

    Atomicity and durability
    ------------------------
    * The temporary file is created in the same directory as the target and
      given a unique name.
    * On successful commit, SafeFile:
        1. flushes Python-level buffers,
        2. calls fsync() on the temporary file descriptor, and
        3. calls MoveFileExW with MOVEFILE_REPLACE_EXISTING and
           MOVEFILE_WRITE_THROUGH to replace the target with the temporary.
    * If any of these steps fail, the replacement is not performed and the
      original target file is left unchanged. The temporary file and any
      placeholder file are removed according to the deletion flags.
    * When BaseException occur that are not SystemExit (e.g. KeyboardInterrupt), SafeFile intentionally
      skips normal file close() on the temporary file and directly closes the
      underlying OS file descriptor instead; in those cases, Python-level
      buffered data may be discarded and the temporary file may be left behind.
    These steps are designed to minimize the chance of ending up with a
    truncated or partially written target file, but they do not guarantee
    survival of the new contents across all power-failure or hardware-failure
    scenarios on all filesystems.

    Locking and concurrency
    -----------------------
    * SafeFile uses an in-process lock keyed by target path so that, within a
      single Python process, multiple SafeFile instances referring to the same
      path are serialized while the instance remains open.
    * This locking is per-process only. Other processes are not coordinated
      and may open or modify the target file concurrently using normal OS
      APIs.
    * The lock is held from successful construction until close() or
      __exit__() releases it. If construction fails, the lock is released
      before the exception is propagated
    * Thread-safety applies both to write and to read-only modes

    File system visibility
    ----------------------
    * If the target does not exist and create_empty=True (the default),
      SafeFile first creates an empty placeholder file at the target path
      before creating the temporary file. This reserves the name and makes
      other processes aware that the path now exists.
    * If create_empty=False, SafeFile will not create such a placeholder.
      In that case, other processes may still unknowingly create or delete the target
      path while SafeFile is writing the temporary file.
      Creating a placeholder file does not guarantee exclusivity.
    * On error, SafeFile attempts to remove the temporary file and, if it
      created a placeholder target file and delete_target=True (the default),
      also attempts to remove that placeholder.

    Attributes and ACLs
    -------------------
    * Replacement is performed using MoveFileExW, which replaces the target
      entry with the temporary file. File attributes, ACLs, and other
      metadata on the original target are not preserved; after a successful
      replacement, they match those of the temporary file.

    Context manager details
    -----------------------
    * SafeFile can be used as a context manager:
          >>> with SafeFile(path, 'w') as f:
          >>>    f.write(...)
      On normal exit from the with-block, writable modes commit the temporary
      file and atomically replace the target.
    * If an Exception subclass is raised inside the with-block, SafeFile
      attempts to close the temporary file, runs cleanup, and then lets the
      exception propagate.
    * If SystemExit is raised inside the with-block, SafeFile treats it as a
      cleanup case as well: it attempts to close the temporary file, runs
      cleanup, and then lets SystemExit propagate.
    * If KeyboardInterrupt, GeneratorExit, or another BaseException that is
      not an Exception subclass and not SystemExit is raised inside the
      with-block, SafeFile avoids normal file close() on the temporary file,
      but closes only the underlying OS file descriptor directly with os.close(),
      skips cleanup, and then lets the exception propagate. In that case,
      temporary files may remain on disk regardless of deletion flags.
    * SafeFile never suppresses exceptions from a with-block

    Additional arguments
    --------------------
    The constructor accepts the following keyword-only options, in addition to
    those accepted by built-in open():

    * create_empty (bool, default True)
        If True, create an empty placeholder target file when the target does
        not exist, so that the name is reserved. If False, no placeholder is
        created; the path may be created or removed by other processes while
        SafeFile is writing the temporary file.

    * delete_temporary (bool, default True)
        If True, delete the temporary file during cleanup. If False, the
        temporary file is left on disk for inspection.

    * delete_target (bool, default True)
        If True and a placeholder target file was created by SafeFile, delete
        that placeholder during cleanup. If create_empty=False, this option
        has no effect.

    * clean_directory (bool, default True)
        If True, SafeFile attempts to remove matching leftover temporary files
        that were opened before when managing the target file.
        Cleanup is performed before opening a new temporary file and works only once per process for the target file in question.
        This cleanup is best-effort and ignores ordinary exceptions.

    Limitations
    -----------
    * Locking is per-process only; it does not coordinate with other processes.
    * Attributes, ACLs, and other metadata of an existing target are not
      preserved when the file is replaced.
    * This class aims to be file-like and proxies most common file methods,
      but it is not a drop-in replacement for every detail of the standard
    * Some close-time errors from the underlying file object are intentionally
      ignored in cleanup-oriented code paths.
    * In certain BaseException paths, temporary files may intentionally remain
      on disk and Python-level buffered data may be discarded.

    Exceptions
    ----------
    * SafeFile propagates exceptions from built-in open(), os.stat(),
      os.fdopen(), mkstemp(), fsync(), and the final replacement step,
      except where noted below.
    * FileNotFoundError is raised for modes that require an existing target
      (for example r+) when the target does not exist.
    * FileExistsError is raised for x or x+ modes when the target already
      exists, including certain races where the target is created by another
      actor after the initial existence check.
    * OSError is raised if the target path exists but is not a regular file,
      and may also be raised by underlying OS file operations.
    * During cleanup, deletion failures are ignored.
    * In read-only close() and in some __exit__() cleanup paths, OSError from
      the underlying file object's close() is ignored.
    * SystemExit raised inside a with-block is not suppressed; it is handled as
      a cleanup-triggering condition and then propagated.
    * KeyboardInterrupt and other BaseException subclasses that are not
      Exception subclasses and not SystemExit are not suppressed; they cause
      SafeFile to skip normal cleanup of the temporary file and then propagate.

    TODO:
    -----
    - Add a resize for a created temp file using mmap.mmap() so that disk space can be also reserved in advance, not only the target name.
      Good practice for large downloads. Need to know whether data will fit in advance and, also, prevent other processes from using the needed space in mid write of our file.
    - Remove locks of closed files to preserve memory (not a priority since we do not expect bursts of SafeFile()s per process)
    """
    locks   = {} # Class attr: Keeps locks of safely opened files making the thing thread-safe per file
    cleaned = {} # Allows temp files leftover cleanup per target but only once in same process
    def __init__ (self, name, mode="r", *args, **kwargs):
        self.mode = mode = mode.lower()
        self.name = name = os.path.abspath(name)
        self.create_empty      = create_empty = kwargs.pop("create_empty", True)
        self.delete_temporary  = kwargs.pop("delete_temporary", True)
        self.delete_target     = kwargs.pop("delete_target", True)
        self.clean_directory   = kwargs.pop("clean_directory", True)
        self.fail_on_lock      = kwargs.pop("fail_on_lock", False)
        self.created = created = False
        self._temp   = None
        self.lock = lock = self.locks.setdefault(name, Lock())
        if self.fail_on_lock and lock.locked():
            raise RuntimeError(f"Target {name!r} already opened")
        lock.acquire()
        writable = self.iswritable()
        if not writable:
            # Just open the target file directly since we will not be making any changes
            try:
                self._file = f = open(name, mode, *args, **kwargs)
            except:
                lock.release()
                raise
            return
        # Avoid possible Windows weirdness surrounding exclusive file creation
        tempmode = mode.replace("x", "w")
        must_copy  = False
        must_exist = False
        if "a" in mode:
            must_copy = True
        elif "+" in mode:
            if "w" in tempmode:
                must_copy = False  # w+ or x+ starts empty
            else:
                must_copy = True   # r+ requires original content
                must_exist = True
        try:
            st = os.stat(name) # If file exists
            if "x" in mode:
                lock.release()
                raise FileExistsError(f"File {name!r} already exists for mode {mode!r}")
            if not S_ISREG(st.st_mode):
                # We deal with files only, best stop immediately if target is wrong
                lock.release()
                raise OSError(f"Target {name!r} is not a regular file")
            # No point copying an empty file, so revide the decision
            must_copy = st.st_size!=0 if must_copy else False
        except FileNotFoundError:
            if must_exist:
                lock.release()
                raise FileNotFoundError(f"File {name!r} does not exist for mode {mode!r}")
            if create_empty:
                try:
                    open(name, "xb").close()
                    self.created = created = True
                except FileExistsError:
                    # Someone else created it after our first stat().
                    # Refresh metadata and continue.
                    try:
                        st = os.stat(name)
                    except FileNotFoundError:
                        lock.release()
                        raise RuntimeError(f"Target {name!r} appeared and disappeared during open()")
                    if "x" in mode:
                        lock.release()
                        raise FileExistsError(f"File {name!r} already exists for mode {mode!r}")
                    if not S_ISREG(st.st_mode):
                        lock.release()
                        raise OSError(f"Target {name!r} is not a regular file")
                    # No point copying if new file is empty
                    must_copy = st.st_size!=0 if must_copy else False
                except:
                    # PermissionError or something else
                    lock.release()
                    raise
        except:
            # PermissionError or something else
            lock.release()
            raise
        dirpath, filename = os.path.split(name)
        if self.clean_directory and not self.cleaned.get(name, False):
            # Remove leftovers
            try:
                for tfp in glob(filename+".*.tmp", root_dir=dirpath):
                    try:
                        os.unlink(os.path.join(dirpath, tfp))
                    except Exception:
                        pass
            except Exception:
                pass
            except:
                lock.release()
                raise
            finally:
                self.cleaned[name] = True
        # Lets first create a temporary file on disk in the same dir as the target
        try:
            fd, tempfile = mkstemp(dir=dirpath, prefix=filename+".", suffix=".tmp")
        except:
            lock.release()
            raise
        self._temp = tempfile
        try:
            if must_copy:
                # Copy original if needed, that is, for "r+" and "a*" modes
                try:
                    os.close(fd)
                except OSError:
                    pass
                try:
                    with open(name, "rb", buffering=0) as rf, open(tempfile, "wb", buffering=0) as wf:
                        copyfileobj(rf, wf, length=1024**2)
                except FileNotFoundError:
                    # This covers source file didn't exist when expected,
                    # or it was removed between placeholder create and copy.
                    # Missing original is fatal for r+, but acceptable for append modes though
                    if must_exist:
                        self._cleanup()
                        raise FileNotFoundError(f"File {name!r} does not exist for mode {mode!r}")
                except Exception:
                    self._cleanup()
                    raise
                try:
                    # Now open the temp file in requested mode
                    f = open(tempfile, tempmode, *args, **kwargs)
                except Exception:
                    self._cleanup()
                    raise
            elif "a" in mode:
                # Best reopen the temp file for append modes, fdopen()'s behaviour is questionable since fd is not opened with O_APPEND flag
                try:
                    os.close(fd)
                except OSError:
                    pass
                try:
                    # Now reopen the temp file in requested mode
                    f = open(tempfile, tempmode, *args, **kwargs)
                except Exception:
                    self._cleanup()
                    raise
            else:
                try:
                    # Now get the temp file object in requested mode from fd (no need for reopening when copy was not needed and mode is not append)
                    f = os.fdopen(fd, tempmode, *args, **kwargs)
                except Exception:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
                    self._cleanup()
                    raise
            self._file = f
        except:
            lock.release()
            raise

    iswritable = lambda self: any((flag in self.mode) for flag in ("w", "a", "x", "+"))

    class _dummyfunc:
        def __init__ (self, func):
            self.func = func
        def __call__ (self, *args, **kwargs):
            raise ValueError("I/O operation on closed file.")
        def __repr__ (self):
            return f"<dummy function {self.func} at {hex(id(self))}"

    def __getattr__ (self, a):
        if a=="buffer" or a=="detach" or a=="reconfigure":
            # This is something you do not mess with in SafeFile()s so just report it as not here
            raise AttributeError(f"'SafeFile' object has no attribute '{a}'")
        f = self._file
        if f is None:
            if a=="tell" or a=="truncate" or a=="flush" or a=="isatty" or a.startswith("read") or a.startswith("write") or a.startswith("seek") or a=="__next__":
                return self._dummyfunc(a)
        try:
            v = getattr(f, a)
            if a in ("newlines", "encoding", "errors", "line_buffering", "write_through"):
                setattr(self, a, v)
            return v
        except AttributeError:
            raise AttributeError(f"'SafeFile' object has no attribute '{a}'")

    def __iter__ (self):
        f = self._file
        if f is None or f.closed:
            raise ValueError("I/O operation on closed file.")
        return iter(f)

    @property
    def closed (self):
        f = self._file
        return f is None or f.closed

    def _cleanup (self):
        if self.delete_temporary and self._temp:
            try:
                os.unlink(self._temp)
            except:
                pass
        if self.created and self.delete_target:
            try:
                os.unlink(self.name)
            except:
                pass
        self.created = False
        self._temp = None

    def _commit (self):
        f = self._file
        try:
            f.flush()
            os.fsync(f.fileno())
            f.close()
            self._file = None
            winKernel.moveFileEx(self._temp, self.name, winKernel.MOVEFILE_REPLACE_EXISTING | winKernel.MOVEFILE_WRITE_THROUGH)
            self.created = False
            self._temp = None
        except Exception:
            self._cleanup()
            raise

    def close (self):
        f = self._file
        if f is None:
            return
        try:
            if self.iswritable():
                self._commit()
                return
            try:
                f.close()
            except OSError:
                pass
            self._file = None
        finally:
            try:
                self.lock.release()
            except RuntimeError:
                pass

    # The underlying __enter__ method returns the wrong object
    # (self._file) so override it to return the wrapper
    def __enter__ (self):
        return self

    # Need to trap __exit__ as well to ensure the temporary file gets
    # moved when used in a with statement
    def __exit__ (self, exc_type, exc_val, exc_tb):
        f = self._file
        if f is None:
            return
        try:
            if not self.iswritable():
                try:
                    f.close()
                except OSError:
                    pass
                self._file = None
                return
            if exc_type is None:
                self._commit()
                return
            if not issubclass(exc_type, Exception):
                # BaseException cases (KeyboardInterrupt, SystemExit, GeneratorExit) in with block:
                if issubclass(exc_type, SystemExit):
                    # This is a special case, in contrast to e.g. KeyboardInterrupt()
                    # in which case we want temp file to remain, regardless the chosen removal policy
                    # but when SystemExit was provoked, we do not want left overs if not specified differently
                    try:
                        f.close()
                    except OSError:
                        pass
                    self._file = None
                    self._cleanup()
                    return
                # KeyboardInterrupt or any other BaseException:
                try:
                    # Avoid descriptor leakage by closing the file, but not performing any writes left in buffer
                    os.close(f.fileno())
                except OSError:
                    pass
                self._file = None
                return
            # Normal Exception in with block; clean things up:
            try:
                f.close()
            except OSError:
                pass
            self._file = None
            self._cleanup()
        finally:
            try:
                self.lock.release()
            except RuntimeError:
                pass

    def __repr__ (self):
        where = self._temp if self._temp else self.name
        state = ("Opened", "Closed")[self.closed]
        return f"<{state} SafeFile(target={self.name!r}, mode={self.mode!r}, current={where!r}) object at {hex(id(self))}>"
