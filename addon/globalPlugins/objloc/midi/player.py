from threading import Thread, Lock
from time import monotonic as time, sleep
from collections import deque

class Note (object):
    __slots__ = ("output", "note", "duration", "velocity", "channel", "started", "playing")
    def __init__ (self, output, note, duration=-1, velocity=127, channel=0):
        self.output = output
        self.note = note
        self.duration = duration if duration<=0 else duration/1000.0
        self.velocity = velocity
        self.channel = channel
        self.playing = False
        self.started = 0

    def play (self):
        if self.playing:
            return
        self.output.note_on(self.note, self.velocity, self.channel)
        self.playing = True
        self.started = time()
        return self

    def stop (self):
        if not self.playing:
            return
        self.output.note_off(self.note, self.velocity, self.channel)
        self.playing = False
        return self

    def shouldStop (self):
        return False if self.playing==False or self.duration<0 else (time()-self.started>=self.duration)

    def __hash__ (self):
        return hash(f"{self.note}:{self.duration}:{self.velocity}:{self.channel}")

class Player (Thread):
    def __init__ (self, output, duration=-1, velocity=127, channel=0):
        Thread.__init__(self)
        self.daemon = True
        self.output = output
        self.duration = duration
        self.velocity = velocity
        self.channel = channel
        self.last_note = None
        self.instruments = {}
        self.volumes = {}
        self.expressions = {}
        self.set_volume(1.0)
        self.set_expression(1.0)
        self.queue = deque()
        self.waiter = Lock()
        self.running = False
        self.start()

    def tick (self):
        try:
            self.waiter.release()
        except:
            pass

    def run (self):
        self.running = True
        while self.running:
            self.waiter.acquire(False)
            with self.waiter:
                keep = deque()
                while self.running:
                    try:
                        note = self.queue.popleft()
                    except:
                        break
                    if note.shouldStop():
                        note.stop()
                    if note.playing:
                        keep.append(note)
                self.queue.extend(keep)

    def quit (self):
        self.running = False
        self.stop()
        self.tick()
        self.join()

    def stop (self):
        while True:
            try:
                note = self.queue.popleft()
            except:
                break
            note.stop()

    def play (self, note, duration=None, velocity=None, channel=None):
        duration = self.duration if duration is None else duration
        velocity = self.velocity if velocity is None else velocity
        channel = self.channel if channel is None else channel
        n = Note(self.output, note, duration, velocity, channel)
        ln = self.last_note
        if ln and ln.playing and ln.note==note and ln.channel==channel:
            ln.started = time()
            ln.duration = duration if duration<0 else duration/1000.0
            if ln.velocity!=velocity:
                ln.output.note_off(note, ln.velocity, channel)
                ln.velocity = velocity
                ln.output.note_on(note, velocity, channel)
        self.queue.append(n.play())
        self.last_note = n

    def pan (self, left=1.0, right=1.0, channel=None):
        channel = self.channel if channel is None else channel
        n = 64 if left+right==0 else int(round((right / (left + right))*127))
        self.output.write_short(0xB0 + channel, 10, n)
        return n

    def get_volume (self, channel=None):
        channel = self.channel if channel is None else channel
        return self.volumes.setdefault(channel, 127)/127.0

    def set_volume (self, volume=1.0, channel=None):
        channel = self.channel if channel is None else channel
        volume = int(volume*127)
        self.output.write_short(0xB0 + channel, 7, volume)
        self.volumes[channel] = volume

    volume = property(get_volume, set_volume)

    def get_expression (self, channel=None):
        channel = self.channel if channel is None else channel
        return self.expressions.setdefault(channel, 127)/127.0

    def set_expression (self, volume=1.0, channel=None):
        channel = self.channel if channel is None else channel
        volume = int(round(volume*127))
        self.output.write_short(0xB0 + channel, 11, volume)
        self.expressions[channel] = volume

    expression = property(get_expression, set_expression)

    def get_instrument (self, channel=None):
        channel = self.channel if channel is None else channel
        return self.instruments.setdefault(channel, 0)

    def set_instrument (self, instrument=0, channel=None):
        channel = self.channel if channel is None else channel
        self.output.set_instrument(instrument, channel)
        self.instruments[channel] = instrument

    instrument = property(get_instrument, set_instrument)
