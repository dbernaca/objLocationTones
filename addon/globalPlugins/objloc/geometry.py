class BBox (object):
    """
    Class for dealing with more complex information of object locations.
    And providing potential operations regarding the same.
    """
    __slots__ = ("L", "T", "W", "H", "X1", "X2", "X3", "X4", "Y1", "Y2", "Y3", "Y4", "TL", "TR", "BR", "BL", "corners")
    def __init__ (self, obj):
        """
        Takes an object and initializes its bounding box.
        """
        loc = obj.location
        self.L, self.T, self.W, self.H = loc
        # Left top corner
        self.X1 = x1 = loc[0]
        self.Y1 = y1 = loc[1]
        self.TL = (x1, y1)
        # Right top corner
        self.X2 = x2 = loc[0]+loc[2]
        self.Y2 = y2 = loc[1]
        self.TR = (x2, y2)
        # Right bottom corner
        self.X3 = x3 = loc[0]+loc[2]
        self.Y3 = y3 = loc[1]+loc[3]
        self.BR = (x3, y3)
        # Left Bottom corner
        self.X4 = x4 = loc[0]
        self.Y4 = y4 = loc[1]+loc[3]
        self.BL = (x4, y4)
        self.corners = ((x1, y1), (x2, y2), (x3, y3), (x4, y4))

    def __contains__ (self, obj):
        """
        Checks whether a point (x, y) or a BBox() of an obj or obj itself given by argument obj,
        occupies the space bounded by this bounding box.
        Returns True if this BBox() and the operand obj share any points between them,
        False otherwise. Intended use is, for example:
        (10, 10) in BBox(obj)
        """
        if isinstance(obj, tuple):
            return (self.X1 <= obj[0] <= self.X2) and (self.Y1 <= obj[1] <= self.Y4)
        obj = obj if isinstance(obj, BBox) else BBox(obj)
        return any((xy in self) for xy in obj.corners)
