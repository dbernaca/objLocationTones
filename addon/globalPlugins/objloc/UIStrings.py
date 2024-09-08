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

# UI strings defined in objLocTones 24.06.1
# =========================================

# A category name in the NVDA settings dialog
SET_CATEGORY = _("Object Location Tones")

SET_POSITIONAL_AUDIO = _("Play positional tones during navigation")

SET_TONE_DURATION = _("Positional tone duration (msec):")

SET_MOUSE_TOLERANCE = _("Mouse point matching tolerance (px):")

SET_MOUSE_MONITOR_TIMEOUT = _("Turn off mouse monitoring automatically after (sec):")

SET_LEFT_VOLUME = _("Left speaker volume:")

SET_RIGHT_VOLUME = _("Right speaker volume:")

SET_SWAP_STEREO_CHANNELS = _("Swap stereo channels")
