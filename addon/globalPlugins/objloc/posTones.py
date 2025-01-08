# Part of Object Location Tones
# This module contains routines to produce positional tones

try:
    from time import monotonic as time
except:
    from time import time

from tones  import beep
from .utils import getDesktopObject

import config
import wx

__all__ = ["minPitch", "maxPitch", "maxVolume", "playCoordinates", "playPoints"]

# Some initial values from NVDA configuration
minPitch  = config.conf['mouse']['audioCoordinates_minPitch']
maxPitch  = config.conf['mouse']['audioCoordinates_maxPitch']
maxVolume = config.conf['mouse']['audioCoordinates_maxVolume']

# Global vars
lastCoords = (-1, -1, 0.0) # Last coordinates played (for avoiding doubleing tones for any reason)
                           # values are (x, y, <tone duration>)
lastPlayed = 0.0           # When was the last tone played (to detect tone doubles requested before their time) (in seconds)

def playCoordinates (x, y, d=40, lVolume=1.0, rVolume=1.0, stereoSwap=False):
    """
    Plays a positional tone for given x and y coordinates,
    relative to current desktop window size.
    If the method is called more than once with same coordinates and already playing,
    the duplicate call will not produce any tones.
    If the coordinates represent a point that is located out of the screen,
    the tone will also not be played.
    """
    global lastCoords, lastPlayed
    # If the same coordinates were just played, and asked to be played again before the last tone ended
    # just don't do it and that is that.
    t = time()
    lx, ly, ld = lastCoords
    if x==lx and ly==ly and t-lastPlayed<=ld:
        return
    screenWidth, screenHeight = getDesktopObject().location[2:]
    if 0 <= x <= screenWidth and 0 <= y <= screenHeight:
        curPitch = minPitch + ((maxPitch - minPitch) * ((screenHeight - y) / float(screenHeight)))
        if stereoSwap:
            right = int((85 * ((screenWidth - float(x)) / screenWidth)) * rVolume)
            left  = int((85 * (float(x) / screenWidth)) * lVolume)
        else:
            left  = int((85 * ((screenWidth - float(x)) / screenWidth)) * lVolume)
            right = int((85 * (float(x) / screenWidth)) * rVolume)
        beep(curPitch, d, left=left, right=right)
        lastPlayed = t
        lastCoords = (x, y, d/1000.0)

def playPoints (delay, points, d=40, lVolume=1.0, rVolume=1.0, stereoSwap=False):
    """
    Plays a sequence of coordinates with delay between them.
    It does it by using wx.CallAfter() and wx.CallLater() to schedule playCoordinates() calls.
    points need to be a sequence of points that can be unpacked to x and y.
    delay is in milliseconds.
    All other arguments are passed to each playCoordinates() call in turn.
    Returns a number of milliseconds necessary to play the next point
    after the playPoints is done, using the same delay.
    Substracting the delay value from returned value will tell you exactly how long will take to play all the points.
    """
    i = iter(points)
    x, y = next(i)
    wx.CallAfter(playCoordinates, x, y, d, lVolume, rVolume, stereoSwap)
    after = d+delay
    for x, y in i:
        wx.CallLater(after, playCoordinates, x, y, d, lVolume, rVolume, stereoSwap)
        after += d+delay
    return after
