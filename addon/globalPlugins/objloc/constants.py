# Constants for Object Location Tones add-on

CARET_VERTICAL   = 0
CARET_HORIZONTAL = 1
CARET_BOTH       = 2
CARET_NONE       = 3

MOUSE_REF_NAVIGATOR = 0
MOUSE_REF_FOCUS     = 1
MOUSE_REF_TLW       = 2
MOUSE_REF_CW        = 3
MOUSE_REF_TLS       = 4
MOUSE_REF_CS        = 5
MOUSE_REF_NONE      = 6
MOUSE_REF_START     = 7

LOCATION_NAVIGATOR_CENTROID = 0
LOCATION_NAVIGATOR_LEFT     = 1
LOCATION_NAVIGATOR_RIGHT    = 2
LOCATION_FOCUS_CENTROID     = 3
LOCATION_FOCUS_LEFT         = 4
LOCATION_FOCUS_RIGHT        = 5

IS_LOCATION_MODE_NAVIGATOR = lambda mode: mode<3
IS_LOCATION_MODE_FOCUS     = lambda mode: mode>2
IS_LOCATION_MODE_CENTROID  = lambda mode: mode==0 or mode==3
IS_LOCATION_MODE_LEFT      = lambda mode: mode==1 or mode==4
IS_LOCATION_MODE_RIGHT     = lambda mode: mode==2 or mode==5