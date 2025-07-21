# Install tasks to preserve settings if the addon was previously installed.
from logHandler import log

import os
import sys
import addonHandler

def findOld ():
    """
    Returns a previously installed addon object of the currently installing add-on.
    None if it wasn't installed before.
    """
    this = addonHandler.getCodeAddon()
    try:
        return next(addonHandler.getAvailableAddons(filterFunc=lambda a:id(a)!=id(this) and a.name==this.name))
    except StopIteration:
        pass

def getSettings (addon):
    """
    Imports the settings module from the installing version of the add-on bundle given by the addon object,
    and returns the active settings.Settings() object with the settings file path
    set to the path of the already installed version of the add-on bundle given by the addon object.
    If the settings file does not exist at the specified location, returns None.
    None is also returned if any other kind of error is encountered, and the error is
    reported in the log. Missing settings file is not reported as this is
    a normal state for old versions of the add-on.
    """
    setpath = os.path.join(addon.path, "globalPlugins", "objloc", "settings", "settings.json")
    if not os.path.isfile(setpath):
        # No old settings file found, so no point continuing
        return
    # We import settings package from the new version of the add-on
    # since it may contain changes needed to pull this off
    if not os.path.isdir(addon.pendingInstallPath):
        log.warning("Object Location Tones bundle for some reason not extracted to '%s, settings cannot be preserved!" % addon.pendingInstallPath)
        return
    packpath = os.path.join(addon.pendingInstallPath,
                            "globalPlugins", "objloc")
    cwd = os.getcwd()
    try:
        # Windows is an odd beast
        os.chdir(packpath)
    except Exception as e:
        log.warning("Unable to change directory to '%s' because of %s, settings will not be preserved!" % (packpath, str(e)))
        return
    sys.path.insert(0, packpath)
    try:
        import settings as S
    except Exception as e:
        log.warning(str(e))
    os.chdir(cwd) # This one should never fail
    sys.path.remove(packpath)
    try:
        obj = S.Settings(setpath)
    except NameError:
        log.warning("Unable to import settings package, settings will not be preserved!")
        return
    except Exception as e:
        log.warning(str(e))
        return
    return obj

def onInstall ():
    log.info("Object Location Tones install started")
    addon = findOld()
    if addon is None:
        log.info("Fresh installation of Object Location Tones detected, proceeding...")
        return
    log.info("There is Object Location Tones already installed version %s, updating..." % addon.version)
    S = getSettings(addon)
    if S is None:
        log.info("Object Location Tones settings file is not found in the previous install or the settings package is unavailable, proceeding...")
        return
    log.info("Object Location Tones settings file found, preserving data...")
    # We load the settings file so that we can modify them to match settings changes in the new addon version.
    # Faster, perhaps even neater, would be just to copy the file itself, so that it gets installed along with new bundle.
    # This way though, we can even define in advance which attributes we would
    # transfer and which not, transform their types if needed, add new ones and delete old, etc. etc.
    # If we just copy the old file, the add-on will have to lose time on each startup to check for differences
    # and make this kind of changes to the settings, adding extra code and overhead.
    # Note: This part of code relies on the old settings file completely, and assumes nobody messed up types by editing it manually
    # Addon will check later though, upon real load and ignore errors
    try:
        # First, get a holder object from the existing file
        inst = S.generate_instance()
        # Add new config to avoid errors at startup and manage backward compatibility with old settings
        if not hasattr(inst, "autoMouse"):
            inst.autoMouse = False
        if not hasattr(inst, "caretTyping"):
            inst.caretTyping = False
        if not hasattr(inst, "caret"):
            inst.caret = True
        if not hasattr(inst, "caretMode"):
            inst.caretMode = (2 if inst.active.value else 3) if hasattr(inst, "active") else 2
            inst.caret.value = True
        if not hasattr(inst, "durationCaret"):
            inst.durationCaret = inst.duration.value if hasattr(inst, "duration") else 40
        if not hasattr(inst, "refPoint"):
            inst.refPoint = 0
        if not hasattr(inst, "midi"):
            inst.midi = False
            inst.instrument = 115
        # Save it into pending install version, so that it gets activated after old add-on removal and renaming of new one:
        setpath = os.path.join(addon.pendingInstallPath, "globalPlugins", "objloc", "settings", "settings.json")
        # Switch settings path to a new file:
        S.path = setpath
        # Save it
        S.save(inst, force=True)
        log.info("Settings preserved. Object Location Tones installation ready!")
    except Exception as e:
        log.warning(str(e))

