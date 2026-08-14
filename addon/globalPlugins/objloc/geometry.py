# Part of Object Location Tones add-on
# Extends capabilities, or replaces their usage where they are too costly, of rects and points from locationHelper.py

from time import monotonic as time

class Point (object):
    __slots__ = ("x", "y", "is_near", "timestamp", "location")
    def __init__ (self, x, y):
        self.x = x
        self.y = y
        self.is_near = self._is_near_func

    def is_near_chebyshev_rect (self, obj, tolerance=0):
        x, y, w, h = obj.location
        cx = x + (w * 0.5)
        cy = y + (h * 0.5)
        hw = (w * 0.5) + tolerance
        hh = (h * 0.5) + tolerance
        return abs(self.x - cx) <= hw and abs(self.y - cy) <= hh

    def is_near_elliptical_rect (self, obj, tolerance=0):
        x, y, w, h = obj.location
        cx = x + (w * 0.5)
        cy = y + (h * 0.5)
        ax = (w * 0.5) + tolerance
        ay = (h * 0.5) + tolerance
        dx = (self.x - cx) / ax
        dy = (self.y - cy) / ay
        return (dx * dx + dy * dy) <= 1.0

    _is_near_func = is_near_chebyshev_rect

    @classmethod
    def set_metric (cls, name):
        cls._is_near_func = getattr(cls, "is_near_" + name + "_rect")

    def set_metric_current (self, name):
        self.is_near = getattr(self, "is_near_" + name + "_rect")

    def stamp (self, timestamp=None):
        self.timestamp = time() if timestamp is None else timestamp
        return self

    def __getattr__ (self, a):
        if a=="location":
            self.location = l = (self.x, self.y, 0, 0)
            return l
        raise AttributeError(f"object 'Point' has no attribute '{a}'")

    def __repr__ (self):
        return f"{self.__class__.__name__}({self.x}, {self.y})"

class StampedPoint (Point):
    __slots__ = ()
    def __init__ (self, x, y, timestamp=None):
        self.x = x
        self.y = y
        self.is_near = self._is_near_func
        self.timestamp = time() if timestamp is None else timestamp

class BBox (object):
    """
    Class for dealing with more complex information of object locations.
    And providing potential operations regarding the same.
    """
    __slots__ = ("location", "L", "T", "W", "H", "X1", "X2", "X3", "X4", "Y1", "Y2", "Y3", "Y4", "TL", "TR", "BR", "BL", "corners")
    def __init__ (self, obj):
        """
        Takes an object and initializes its bounding box.
        """
        self.location = loc = obj.location
        self.L, self.T, self.W, self.H = loc
        # Left top corner
        self.X1 = x1 = loc[0]
        self.Y1 = y1 = loc[1]
        self.TL = (x1, y1)
        # Right top corner
        self.X2 = x2 = loc[0]+loc[2]
        self.Y2 = y2 = y1 # loc[1]
        self.TR = (x2, y2)
        # Right bottom corner
        self.X3 = x3 = x2 # loc[0]+loc[2]
        self.Y3 = y3 = loc[1]+loc[3]
        self.BR = (x3, y3)
        # Left Bottom corner
        self.X4 = x4 = x1 # loc[0]
        self.Y4 = y4 = y3 # loc[1]+loc[3]
        self.BL = (x4, y4)
        self.corners = ((x1, y1), (x2, y2), (x3, y3), (x4, y4))

    def __contains__ (self, point: tuple):
        """
        Checks whether a point (x, y) given by argument point as a tuple (obviously),
        belongs to space bounded by this bounding box, edges and corners included.
        Returns True if this BBox() and the operand point occupy the same space,
        False otherwise. Intended use is, for example:
        (10, 10) in BBox(obj)
        """
        return (self.X1 <= point[0] <= self.X2) and (self.Y1 <= point[1] <= self.Y4)

    def overlaps (self, other):
        """
        Checks if this BBox() overlaps another BBox() and returns True
        if they intersect anywhere. The argument other can also be a NVDAObject() like instance
        containing the attribute location with appropriate rect.
        """
        other = other if isinstance(other, BBox) else BBox(other)
        return (self.X1 <= other.X2 and other.X1 <= self.X2
                and self.Y1 <= other.Y3 and other.Y1 <= self.Y3)

    def __repr__ (self):
        o = self.location.__repr__()
        return self.__class__.__name__+o[o.find("("):]
