import re


class _Comparable(object):

    """Implements rich comparison if __lt__ and __eq__ are provided."""

    def __gt__(self, other):
        return not self < other and not self == other

    def __le__(self, other):
        return self < other or self == other

    def __ne__(self, other):
        return not self == other

    def __ge__(self, other):
        return self > other or self == other


class VersionError(Exception):
    pass


_re = re.compile('(\d+)\.(\d+)\.(\d+)'  # minor, major, patch
                 '(-[0-9A-Za-z-\.]+){0,1}'  # pre-release
                 '(\+[0-9A-Za-z-\.]+){0,1}'  # build
                 '$')


class _Seq(_Comparable):

    """Sequence of identifies that could be compared according to semver."""

    def __init__(self, seq):
        self.seq = seq

    def __lt__(self, other):
        #if self.seq == [] or other.seq == []:
        #    return other.seq == []
        if len(self.seq) != len(other.seq):
            raise NotImplementedError(self.seq, other.seq)
        assert set([int, str]) >= set(map(type, self.seq))
        for s, o in zip(self.seq, other.seq):
            if type(s) is int and type(o) is int:
                if s < o:
                    return True
            elif type(s) is int or type(o) is int:
                return type(s) is int
            elif s != o:
                return s < o

    def __eq__(self, other):
        return self.seq == other.seq


def _try_int(s):
    assert type(s) is str
    try:
        return int(s)
    except ValueError:
        return s


def _make_group(g):
    return [] if g is None else map(_try_int, g[1:].split('.'))


class Version(_Comparable):

    def __init__(self, version):
        match = _re.match(version)
        if not match:
            raise VersionError('invalid version %r' % version)
        self.major, self.minor, self.patch = map(int, match.groups()[:3])
        self.pre_release = _make_group(match.groups()[3])
        self.build = _make_group(match.groups()[4])

    def __str__(self):
        s = '.'.join(str(s) for s in self._mmp())
        if self.pre_release:
            s += '-%s' % '.'.join(str(s) for s in self.pre_release)
        if self.build:
            s += '+%s' % '.'.join(str(s) for s in self.build)
        return s

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.__str__())

    def _mmp(self):
        return [self.major, self.minor, self.patch]

    def __lt__(self, other):
        if self._mmp() == other._mmp():
            if self.pre_release and other.pre_release:
                if _Seq(self.pre_release) < _Seq(other.pre_release):
                    return True
            elif self.pre_release or other.pre_release:
                return bool(self.pre_release)
            elif self.build and other.build:
                if _Seq(self.build) < _Seq(other.build):
                    return True
            elif self.build or other.build:
                return bool(other.build)
        return self._mmp() < other._mmp()

    def __eq__(self, other):
        return all([self._mmp() == other._mmp(),
                    self.pre_release == other.pre_release])
