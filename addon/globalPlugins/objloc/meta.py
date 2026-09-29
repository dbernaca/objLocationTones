# Part of Object Location Tones add-on
# Because I love this kind of quasi meta programming.
# Like with settings package, but for broader use

class AutoAll (list):
    """
    Implements a way to construct __all__ as you code, instead of adding stuff manually.
    """
    __slots__ = ("_namespace", "_stack")
    def __init__(self, namespace, names=()):
        list.__init__(self, names)
        self._namespace = namespace

        # Element zero holds the implicit include()/exclude()
        # checkpoint. "__all__" is added because assignment to
        # __all__ occurs only after this constructor returns.
        self._stack = [[set(namespace) | {"__all__"}, None]]

    def _apply (self, names, include):
        if include:
            self.extend(names.difference(self))
        else:
            self[:] = set(self).difference(names)

        # A completed nested operation must not be processed again
        # by its enclosing regions.
        for frame in self._stack[1:]:
            frame[0].update(names)

        # This is now the most recently completed boundary.
        self._stack[0][0] = set(self._namespace)

    def begin (self):
        self._stack.append([
            set(self._namespace),
            True,
        ])

    def beginExclude (self):
        self._stack.append([
            set(self._namespace),
            False,
        ])

    def end (self):
        if len(self._stack) == 1:
            raise RuntimeError("end() without matching begin()")
        start, include = self._stack.pop()
        names = set(self._namespace).difference(start)
        self._apply(names, include)
        return self

    endExclude = end

    def include (self):
        """
        Include names since construction or the last boundary.
        """
        current = set(self._namespace)
        names = current.difference(self._stack[0][0])
        self._apply(names, True)
        return self

    def exclude (self):
        """
        Exclude names since construction or the last boundary.
        """
        current = set(self._namespace)
        names = current.difference(self._stack[0][0])
        self._apply(names, False)
        return self

    def finalize (self):
        """
        Validate that all regions are closed and exports exist.
        """
        if len(self._stack) != 1:
            raise RuntimeError(
                f"{len(self._stack) - 1} export region(s) not closed",
            )
        for name in self:
            if not isinstance(name, str):
                raise TypeError(
                    f"__all__ entries must be strings, got {name!r}",
                )
            if name not in self._namespace:
                raise NameError(
                    f"__all__ contains undefined name {name!r}",
                )
        return self

    def __enter__ (self):
        self.begin()
        return self

    def __exit__ (self, excType, excValue, traceback):
        if excType is None:
            self.end()
        else:
            self._stack.pop()

        return False

