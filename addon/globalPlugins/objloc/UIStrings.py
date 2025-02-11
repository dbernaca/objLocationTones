# This module is part of Object Location Tones NVDA add-on
# It contains all of the interface strings, so that translating the add-on may be as easy as possible
#
# Translators: You do not need to look anywhere else within the package for content to translate
# All messages are commented and denoted clearly, with their context explained.
# Groups of UI strings are separated by the add-on version, so if a new string
# appears in a new version that needs translating, you will see it at once.
# All new strings will be added at the end of this module

import addonHandler

try:
    addonHandler.initTranslation()
except addonHandler.AddonError:
    # The objLocTones was called from scratchpad, so no translations
    pass

# UI strings defined in objLocTones 24.06.0
# =========================================

# Input gestures dialog category label for objLocTones.
IG_CATEGORY = _("Object Location Tones") 

# Focused object outline report gesture description in the input gesture dialog
IG_OUTLINE = _("Report outline of currently focused object via positional tones")

# Parent object outline report gesture description in the input gesture dialog
IG_PARENT_OUTLINE = _("Report outline of a parent of currently focused object via positional tones")

# The toggle mouse location monitoring gesture description in the input gesture dialog
IG_TOGGLE_MOUSE_MONITOR = _("Toggle a mouse cursor position in relation to focused object location reporting via positional tones")

# Input dialog gesture description for on request of mouse cursor location
IG_MOUSE_POSITION = _("Play a positional tone for a mouse cursor")

# The gesture description for on request object location in the input gesture dialog
IG_OBJECT_LOCATION = _("Play a positional tone for currently focused object")

# The Object Location Tones toggle gesture description in the input gesture dialog
IG_TOGGLE_LOCATION_REPORTING = _("Toggle automatic auditory description of object locations via positional tones")

# The Object Location Tones toggle of caret reporting gesture description in the input gesture dialog
IG_TOGGLE_CARET_LOCATION_REPORTING = _("Toggle caret location reporting via positional tones")

# Description for cycling through caret reporting modes in the input gesture dialog
IG_CYCLE_CARET_MODE = _("Cycle through caret reporting modes")

# ui.message() when fetching parent object for positional audio and there is no parent to fetch
MSG_PARENT_NOT_AVAILABLE = _("Parent object not available")

# ui.message() in reporting parent outline script
# The message is dynamic and thus only partially translatable
# %s will be fetched using NVDA's API, so the content translation will be managed by NVDA
# %i is a level of the ancestor in the ancestors tree
# so, only a word/words regarding explaining that number for
# the NVDA's object description
# To understand completely, use the parent outline feature by
# pressing Ctrl+Alt+Shift+Numpad Delete,
MSG_ANCESTOR = "%s, "+_("ancestor")+" %i"

# ui.message() in all cases when the location of an object, for any reason, cannot be detected
MSG_LOCATION_UNAVAILABLE = _("Location unavailable")

# ui.message() in mouse monitoring, when triggered, and the mouse cursor
# is already at the position of the focused object
MSG_MOUSE_ALREADY_THERE = _("Mouse already there")

# ui.message() when user cancels the mouse monitoring by triggering the script via gesture
MSG_MOUSE_MONITOR_CANCELLED = _("Mouse location monitoring cancelled")

# ui.message() when the mouse monitoring stops automatically after the mouse is stationary for too long
MSG_MOUSE_MONITOR_STOPPED = _("Mouse location monitoring stopped")

# ui.message() during the mouse monitoring when the mouse enters the focused object area
MSG_ENTERING = _("Entering focused object")

# ui.message() during the mouse monitoring when the mouse exits the focused object area
MSG_EXITING = _("Exiting focused object")

# ui.message() when during the mouse monitoring the mouse cursor is brought to the denoted location of the focused object
MSG_LOCATION_REACHED = _("Location reached")

# ui.message() when positional tones are switched on via gesture
MSG_POSITIONAL_TONES_ON = _("Positional tones on")

# ui.message() when positional tones are switched off via gesture
MSG_POSITIONAL_TONES_OFF = _("Positional tones off")

# ui.message() when positional tones for a caret are switched on via gesture
MSG_CARET_TONES_ON = _("Caret location reporting on")

# ui.message() when positional tones for a caret are switched off via gesture
MSG_CARET_TONES_OFF = _("Caret location reporting off")

# UI strings defined in objLocTones 24.06.1
# =========================================

# A category name in the NVDA settings dialog
SET_CATEGORY = _("Object Location Tones")

SET_POSITIONAL_AUDIO = _("Play positional tones during object navigation")

SET_TONE_DURATION = _("Positional tone duration (msec):")

SET_MOUSE_TOLERANCE = _("Mouse point matching tolerance (px):")

SET_MOUSE_MONITOR_TIMEOUT = _("Turn off mouse monitoring automatically after (sec):")

SET_MOUSE_MONITOR_AUTO_START = _("Start mouse location monitoring automatically")

SET_LEFT_VOLUME = _("Left speaker volume:")

SET_RIGHT_VOLUME = _("Right speaker volume:")

SET_SWAP_STEREO_CHANNELS = _("Swap stereo channels")

# UI strings defined in objLocTones 24.07.0
# =========================================

SET_CARET = _("Play positional tones for caret location")

SET_TONE_DURATION_CARET = _("Tone duration for caret location reporting (msec):")

SET_CARET_TYPING = _("Report caret location while typing")

# Label for the caret reporting mode in settings and in message when using script
SET_CARET_REPORT = _("Caret reporting mode:")

SET_CARET_VERTICAL = _("Lines")

SET_CARET_HORIZONTAL = _("Columns")

SET_CARET_BOTH = _("Lines And Columns")

SET_CARET_NONE = _("None")

# DO NOT CHANGE THE ORDER OF CHOICES
# Choice detection is index based and hard-coded because of settings and translations
# The index is saved to settings so that it can be unrelated to any locale
SET_CARET_CHOICES = [SET_CARET_VERTICAL, SET_CARET_HORIZONTAL, SET_CARET_BOTH, SET_CARET_NONE]

# Label in settings for the mouse monitoring second beep
SET_MOUSE_REF_POINT = _("Mouse monitoring reference point:")

# Mouse reference point will be the focused object's location (default behaviour)
SET_MOUSE_REF_FOCUS = _("Focused object's location")

# Mouse reference point: Top Left of the Window
SET_MOUSE_REF_TLW = _("Top left corner of the application's root window")

# Mouse reference point: Centre of the window
SET_MOUSE_REF_CW = _("Centre of the application's root window")

# Mouse reference point: Top left of the screen
SET_MOUSE_REF_TLS = _("Top left corner of the screen")

# Mouse reference point: Centre of the screen
SET_MOUSE_REF_CS = _("Centre of the screen")

# Mouse reference point: none will be used
SET_MOUSE_REF_NONE = _("NONE")

# DO NOT CHANGE THE ORDER OF CHOICES
# Choice detection is index based and hard-coded because of settings and translations
# The index is saved to settings so that it can be unrelated to any locale
SET_MOUSE_REF_CHOICES = [SET_MOUSE_REF_FOCUS, SET_MOUSE_REF_TLW, SET_MOUSE_REF_CW, SET_MOUSE_REF_TLS, SET_MOUSE_REF_CS, SET_MOUSE_REF_NONE]

# The grouping labels in settings panel
SET_GROUP_NAVIGATION = _("Navigation")

SET_GROUP_CARET = _("Caret")

SET_GROUP_MOUSE = _("Mouse")

SET_GROUP_TONES = _("Tones")

SET_GROUP_AUDIO = _("Audio")

SET_RESTORE_DEFAULTS = _("Restore defaults...")