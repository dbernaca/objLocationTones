# Install tasks to preserve settings if the addon was previously installed.
from logHandler import log

import os
import sys
import addonHandler

def findOld ():
    try:
        return next(addonHandler.getAvailableAddons(filterFunc=lambda a:a.name=="objLocTones"))
    except:
        pass

def getSettings (addon):
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
    sys.path.append(packpath)
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
    log.info("There is Object Location Tones already installed, updating...")
    S = getSettings(addon)
    if S is None:
        log.info("Object Location Tones settings file is not found in the previous install or the settings package is unavailable, proceeding...")
        return
    log.info("Object Location Tones settings file found, preserving data...")
    # We load the settings so that we can modify them in future
    # if ever needed. Faster, perhaps even neater, would be to move the file itself, and put it back later.
    # This way though, we can even define in advance which attributes we would
    # transfer and which not, transform their types if needed, add new ones and delete old, etc. etc.
    # Note: This part of code relies on the old settings file completely, and assumes nobody messed up types by editing it manually
    # Addon will check later though, upon real load and ignore errors
    try:
        # First, get a holder object from the existing file
        inst = S.generate_instance()
        # Save it into pending install version, so that it gets activated after old add-on removal and renaming of new one:
        setpath = os.path.join(addon.pendingInstallPath, "globalPlugins", "objloc", "settings", "settings.json")
        # Switch settings path to a new file:
        S.path = setpath
        # Save it
        S.save(inst, force=True)
        log.info("Settings preserved. Object Location Tones installation ready!")
    except Exception as e:
        log.warning(str(e))

