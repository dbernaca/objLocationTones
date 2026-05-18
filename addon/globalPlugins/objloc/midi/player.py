from threading import Thread, Condition
from time import monotonic as time
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
        return False if self.playing==False or self.duration<0 else ((time()-self.started)>=self.duration)

    def __hash__ (self):
        return hash(f"{self.note}:{self.duration}:{self.velocity}:{self.channel}")

    def __eq__ (self, other):
        return isinstance(other, Note) and self.note==other.note and self.channel==other.channel

class Player (Thread):
    def __init__ (self, output, duration=-1, velocity=127, channel=0):
        Thread.__init__(self)
        self.daemon = True
        self.output = output
        self.duration = duration
        self.velocity = velocity
        self.channel = channel
        self.instruments = {}
        self.volumes     = {}
        self.expressions = {}
        self.bends       = {}
        self.set_volume(1.0)
        self.set_expression(1.0)
        self.set_pitch_bend(0.0)
        self.queue   = deque()
        self.waiter  = Condition()
        self.running = False
        self.start()

    def tick (self):
        with self.waiter:
            self.waiter.notify()

    def run (self):
        waiter = self.waiter
        self.running = True
        with waiter:
            waiter.wait()
        while self.running:
            with waiter:
                timeouts = deque()
                keep = deque()
                while self.queue and self.running:
                    note = self.queue.popleft()
                    if note.playing and note.duration>=0:
                        remains = note.duration -(time()-note.started)
                        if remains>0:
                            timeouts.append(remains)
                        else:
                            note.stop()
                            continue
                    elif note.shouldStop():
                        note.stop()
                        continue
                    if note.playing:
                        keep.append(note)
                self.queue.extend(keep)
                if timeouts:
                    waiter.wait(min(timeouts))
                else:
                    waiter.wait()

    def quit (self):
        self.running = False
        self.stop()
        with self.waiter:
            self.waiter.notify_all()
        self.join()

    def stop (self):
        waiter = self.waiter
        with waiter:
            while True:
                try:
                    note = self.queue.popleft()
                except:
                    break
                note.stop()
            waiter.notify()

    def play (self, note, duration=None, velocity=None, channel=None):
        duration = self.duration if duration is None else duration
        velocity = self.velocity if velocity is None else velocity
        channel = self.channel if channel is None else channel
        waiter = self.waiter
        n = Note(self.output, note, duration, velocity, channel)
        with waiter:
            try:
                ln = self.queue[-1]
            except:
                ln = None
            if ln==n and ln.playing:
                ln.started = time()
                ln.duration = duration if duration<=0 else duration/1000.0
                if ln.velocity!=velocity:
                    ln.output.note_off(note, ln.velocity, channel)
                    ln.velocity = velocity
                    ln.output.note_on(note, velocity, channel)
                waiter.notify()
                return
            self.queue.append(n.play())
            waiter.notify()

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

    def get_pitch_bend (self, channel=None):
        channel = self.channel if channel is None else channel
        value = self.bends.setdefault(channel, 0)
        return int(value/8192) if value < 0 else int(value/8191)

    def set_pitch_bend (self, bend=0, channel=None):
        channel = self.channel if channel is None else channel
        value = int(bend*8192 if bend<0 else bend*8191)
        self.output.pitch_bend(value, channel)
        self.bends[channel] = value

    pitch_bend = property(get_pitch_bend, set_pitch_bend)

