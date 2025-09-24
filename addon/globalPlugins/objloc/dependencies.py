# Part of Object Location Tones add-on
# This module deals with any dependency that may or may not be present.
# Most likely other add-ons that Object Location Tones is interoperating with
# Functions present here are intended to detect, enable and disable such interoperability
# This interface is still in proof of concept stage and will be subject to violent changes

from core import postNvdaStartup
from NVDAState import _TrackNVDAInitialization
from logHandler import log
from threading import Event
from collections import deque

import addonHandler

states = {}

isNVDAInitialized = _TrackNVDAInitialization.isInitializationComplete

def findAddon (addonId):
    try:
        return next(addonHandler.getAvailableAddons(filterFunc=lambda a:a.name==addonId))
    except StopIteration:
        pass

def checkAddonUsability (addonId, logging=True, running=False):
    if isinstance(addonId, str):
        if logging:
            log.info(addonId+" add-on requested for Object Location Tones. Checking...")
        addon = findAddon(addonId)
        if not addon:
            if logging:
                log.warning(addonId+" not found")
            return False
    else:
        addon = addonId
        addonId = addon.name
        if logging:
            log.info(addonId+" add-on requested for Object Location Tones. Checking...")
    if addon.isPendingInstall:
        if logging:
            log.warning(addonId+" is pending install. Try after restarting NVDA.")
        return False
    if addon.isPendingRemove:
        if logging:
            log.warning(addonId+" is going to be removed. Usage blocked.")
        return False
    if addon.isDisabled:
        if logging:
            log.warning(addonId+" is disabled. Enable it first.")
        return False
    if addon.isBlocked:
        if logging:
            log.warning(addonId+" is blocked")
        return False
    if running and not addon.isRunning:
        if logging:
            log.warning(addonId+" is not running")
        return False
    return True

class AddonPublicInterface:
    def __init__ (self, id, *args, **kwargs):
        self.id   = id
        self.args = args
        self.kwargs = kwargs
        self.logging = True
        self.running = False

    def check (self):
        return checkAddonUsability(self.id, logging=self.logging, running=self.running)

    def enabled (self):
        try:
            return states[self.id].isSet()
        except KeyError:
            return False

    def enable (self, *args, **kwargs):
        raise NotImplementedError

    def disable (self, *args, **kwargs):
        raise NotImplementedError

    def terminate (self):
        raise NotImplementedError

class ETN (AddonPublicInterface):
    def __init__ (self):
        AddonPublicInterface.__init__(self, "easyTableNavigator")
        self.running = True

    def enable (self, onToggleNav=None, onNavigation=None):
        ETN = findAddon(self.id)
        if not ETN:
            if self.logging:
                log.warning("easyTableNavigator not found")
            return False
        if not self.check():
            return False
        try:
            from globalPlugins.easyTableNavigator.extpoints import action_easyTableNavigator, action_toggleTableNav, action_tableNavigation, flag_tableNav
            from globalPlugins.easyTableNavigator import extpoints
        except:
            if self.logging:
                log.warning("Easy Table Navigator version %s cannot be used by third party. Please update the add-on." % ETN.version)
            return False
        if onToggleNav:
            action_toggleTableNav.register(onToggleNav)
        if onNavigation:
            action_tableNavigation.register(onNavigation)
        self.tableNavAvailable = extpoints.tableNavAvailable
        self._tableNav    = flag_tableNav
        self.onToggleNav  = onToggleNav
        self.onNavigation = onNavigation
        action_easyTableNavigator.register(self.eventManager)
        return True

    @property
    def tableNav (self):
        try:
            return self._tableNav.isSet()
        except AttributeError:
            return False

    def disable (self):
        try:
            from globalPlugins.easyTableNavigator.extpoints import action_toggleTableNav, action_tableNavigation
        except:
            if self.logging:
                log.warning("Critical error for Easy Table Navigator support: Version mismatch!")
            return False
        if self.onToggleNav:
            action_toggleTableNav.unregister(self.onToggleNav)
        if self.onNavigation:
            action_tableNavigation.unregister(self.onNavigation)
        return True

    def terminate (self):
        if self.enabled():
            self.disable()
        try:
            del self.onToggleNav
        except AttributeError:
            pass
        try:
            del self.onNavigation
        except AttributeError:
            pass
        try:
            del self.tableNavAvailable
        except AttributeError:
            pass
        try:
            del self._tableNav
        except AttributeError:
            pass

    def eventManager (self, event):
        if event=="Terminated":
            self.terminate()

easyTableNavigator = ETN()

_enabq = deque()
def _postStartupEnabler ():
    import wx
    while _enabq:
        try:
            addonId, func, flag, args, kwargs = _enabq.popleft()
        except:
            break
        state = func(*args, **kwargs)
        if state:
            flag.set()
            log.info("Support for %s add-on in Object Location Tones enabled successfully" % addonId)
        else:
            log.info("Support for %s in Object Location Tones failed to initiate" % addonId)
    _enabq.clear()
    wx.CallAfter(postNvdaStartup.unregister, _postStartupEnabler)

postNvdaStartup.register(_postStartupEnabler)

def enableAddonSupport (addonId, *args, **kwargs):
    e = states.setdefault(addonId, Event())
    e.clear()
    func = getattr(globals()[addonId], "enable")
    if isNVDAInitialized():
        state = func(*args, **kwargs)
        if state:
            e.set()
            log.info("Support for %s add-on in Object Location Tones enabled successfully" % addonId)
        else:
            log.info("Support for %s in Object Location Tones failed to initiate" % addonId)
        return state
    _enabq.append((addonId, func, e, args, kwargs))

def disableAddonSupport (addonId, *args, **kwargs):
    addon = states.get(addonId)
    if addon is None:
        log.warning(addonId+" was never requested")
        return False
    if not addon.isSet():
        log.warning(addonId+" was not yet enabled. Nothing to disable.")
        return False
    state = getattr(globals()[addonId], "disable")(*args, **kwargs)
    if not state:
        log.info("Unable to disable support for %s add-on in Object Location Tones" % addonId)
        return False
    addon.clear()
    log.info("Support for %s add-on in Object Location Tones disabled successfully" % addonId)
    return True

def isAddonSupportEnabled (addonId):
    addon = states.get(addonId)
    if addon is None:
        log.warning(addonId+" was never requested")
        return False
    if not isNVDAInitialized():
        if addon.isSet():
            return True
        log.warning("NVDA not initialized yet. "+addonId+" is still pending support enabling")
        return False
    return addon.isSet()
