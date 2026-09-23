# Part of Object Location Tones
# This module contains routines to produce positional tones

from time   import monotonic as time
from tones  import beep
from .utils import getDesktopObject
from .      import midi
from .midi  import general_midi_instruments

import config
import wx

__all__ = ["minPitch", "maxPitch", "maxVolume", "play", "playCoordinates", "playPoints"]

# Some initial values from NVDA configuration
minPitch  = config.conf['mouse']['audioCoordinates_minPitch']
maxPitch  = config.conf['mouse']['audioCoordinates_maxPitch']
maxVolume = config.conf['mouse']['audioCoordinates_maxVolume']

class _play:
    __slots__ = ("lastCoords", "lastPlayed", "lVolume", "rVolume", "stereoSwap", "generator")
    def __init__ (self):
        self.lastCoords = (-1, -1, 0.0) # Last coordinates played (for avoiding doubleing tones for any reason)
                                        # values are (x, y, <tone duration>)
        self.lastPlayed = 0.0           # When was the last tone played (to detect tone doubles requested before their time) (in seconds)
        self.lVolume    = 1.0
        self.rVolume    = 1.0
        self.stereoSwap = False

    def coordinates (self, x, y, d=40):
        """
        Plays a positional tone for given x and y coordinates,
        relative to current desktop window size.
        If the method is called more than once with same coordinates and already playing,
        the duplicate call will not produce any tones.
        If the coordinates represent a point that is located out of the screen,
        the tone will also not be played.
        """
        # If the same coordinates were just played, and asked to be played again before the last tone ended
        # just don't do it and that is that.
        t = time()
        lx, ly, ld = self.lastCoords
        if x==lx and ly==ly and t-self.lastPlayed<=ld:
            return
        screenWidth, screenHeight = getDesktopObject().location[2:]
        if 0 <= x <= screenWidth and 0 <= y <= screenHeight:
            curPitch = minPitch + ((maxPitch - minPitch) * ((screenHeight - y) / float(screenHeight)))
            if self.stereoSwap:
                right = int((85 * ((screenWidth - float(x)) / screenWidth)) * self.rVolume)
                left  = int((85 * (float(x) / screenWidth)) * self.lVolume)
            else:
                left  = int((85 * ((screenWidth - float(x)) / screenWidth)) * self.lVolume)
                right = int((85 * (float(x) / screenWidth)) * self.rVolume)
            self.generator(curPitch, d, left=left, right=right)
            self.lastPlayed = t
            self.lastCoords = (x, y, d/1000.0)

    def points (self, delay, points, d=40):
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
        wx.CallAfter(self.coordinates, x, y, d)
        after = d+delay
        for x, y in i:
            wx.CallLater(after, self.coordinates, x, y, d)
            after += d+delay
        return after

play = _play()
playCoordinates = play.coordinates
playPoints      = play.points
play.generator = beep

player = None

def note (pitch, duration, left=100, right=100):
    note = int(round(((pitch-minPitch)/maxPitch)*127))
    #note  = int(scale)
    #bend  = scale-note
    player.pan(left, right)
    #player.set_pitch_bend(bend)
    v = ((left/85) +(right/85))*0.8
    player.set_expression(v)
    player.play(note, duration)

def none (pitch, duration, left, right):
    pass

def setGenerator (name="NVDA", device=None):
    global player
    if player:
        player.quit()
        if isinstance(player, midi.Player):
            midi.quit()
        player = None
    if name=="NVDA":
        play.generator = beep
    elif name=="MIDI":
        midi.init()
        device = midi.get_default_output_id() if device is None else device
        output = midi.Output(device)
        player = midi.Player(output)
        play.generator = note
    elif name=="None":
        play.generator = none
