# Install tasks to preserve settings if the addon was previously installed.
from logHandler import log

import os
import sys
import addonHandler
import globalVars

def findOld ():
    for addon in addonHandler.getAvailableAddons():
        if addon.name=="objLocTones":
            return addon

def getSettings (addon):
    path = os.path.join(addon.path, "globalPlugins", "objloc")
    if not os.path.isdir(os.path.join(path, "settings")):
        return
    cwd = os.getcwd()
    os.chdir(path)
    sys.path.append(path)
    try:
        import settings as S
    except:
        pass
    os.chdir(cwd)
    sys.path.remove(path)
    try:
        obj = S.Settings()
    except Exception as e:
        log.warning(str(e))
        return
    # There is a very low possibility that there is no old settings file, so, no point continuing:
    if not os.path.isfile(obj.path):
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
        log.info("Object Location Tones settings file is not found in the previous install, proceeding...")
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
        if not os.path.isdir(addon.pendingInstallPath):
            log.warning("Object Location Tones bundle for some reason not extracted to '%s, settings cannot be preserved!" % addon.pendingInstallPath)
            return
        path = os.path.join(addon.pendingInstallPath,
                            "globalPlugins", "objloc", "settings", os.path.basename(S.path))
        # Switch settings path to new file:
        S.path = path
        # In the future, the settings module from pending install needs to be imported,
        # so that the new settings is synchronized with any possible changes in settings protocol,
        # and used to save the instance.
        # For now though, reuse the already instanced object to save it into new file:
        S.save(inst, force=True)
        log.info("Object Location Tones installation ready!")
    except Exception as e:
        log.warning(str(e))

