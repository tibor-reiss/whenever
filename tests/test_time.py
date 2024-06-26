import pickle
import re
from datetime import time as py_time, timezone as py_timezone

import pytest

from whenever import Date, NaiveDateTime, Time

from .common import AlwaysEqual, AlwaysLarger, AlwaysSmaller, NeverEqual


class TestInit:

    def test_all_args(self):
        t = Time(1, 2, 3, 4_000)
        assert t.hour == 1
        assert t.minute == 2
        assert t.second == 3
        assert t.microsecond == 4_000

    def test_all_kwargs(self):
        assert Time(hour=1, minute=2, second=3, microsecond=4_000) == Time(
            1, 2, 3, 4_000
        )

    def test_defaults(self):
        assert Time() == Time(0, 0, 0, 0)

    def test_out_of_range(self):
        with pytest.raises(ValueError):
            Time(24, 0, 0, 0)
        with pytest.raises(ValueError):
            Time(0, 60, 0, 0)
        with pytest.raises(ValueError):
            Time(0, 0, 60, 0)
        with pytest.raises(ValueError):
            Time(0, 0, 0, 1_000_000)


@pytest.mark.parametrize(
    "t, expect",
    [
        (Time(1, 2, 3, 40_000), "01:02:03.04"),
        (Time(1, 2, 3), "01:02:03"),
        (Time(1, 2), "01:02:00"),
        (Time(1), "01:00:00"),
    ],
)
def test_canonical_format(t, expect):
    assert str(t) == expect
    assert t.canonical_format() == expect
    assert t.common_iso8601() == expect


def test_repr():
    t = Time(1, 2, 3, 40_000)
    assert repr(t) == "Time(01:02:03.04)"


class TestFromCanonicalFormat:

    @pytest.mark.parametrize(
        "input, expect",
        [
            ("00:00:00.000000", Time()),
            ("01:02:03.004000", Time(1, 2, 3, 4_000)),
            ("23:59:59.999999", Time(23, 59, 59, 999_999)),
            ("23:59:59.99", Time(23, 59, 59, 990_000)),
            ("23:59:59", Time(23, 59, 59)),
        ],
    )
    def test_valid(self, input, expect):
        assert Time.from_canonical_format(input) == expect
        assert Time.from_common_iso8601(input) == expect

    @pytest.mark.parametrize(
        "input",
        [
            "01:02:03.004.0",
            "01:02:03+00:00",
            "32:02:03",
            "22:72:03",
            "22:72:93",
            "garbage",
        ],
    )
    def test_invalid(self, input):
        with pytest.raises(
            ValueError,
            match=r"Could not parse.*canonical format.*"
            + re.escape(repr(input)),
        ):
            Time.from_canonical_format(input)

        with pytest.raises(
            ValueError,
            match=r"Could not parse.*ISO 8601.*" + re.escape(repr(input)),
        ):
            Time.from_common_iso8601(input)


def test_eq():
    t = Time(1, 2, 3, 4_000)
    same = Time(1, 2, 3, 4_000)
    different = Time(1, 2, 3, 5_000)

    assert t == same
    assert not t == different
    assert not t == NeverEqual()
    assert t == AlwaysEqual()

    assert not t != same
    assert t != different
    assert t != NeverEqual()
    assert not t != AlwaysEqual()

    assert hash(t) == hash(same)
    assert hash(t) != hash(different)


class TestFromPyTime:
    def test_valid(self):
        assert Time.from_py_time(py_time(1, 2, 3, 4)) == Time(1, 2, 3, 4)

    def test_tzinfo(self):
        with pytest.raises(ValueError):
            Time.from_py_time(py_time(1, 2, 3, 4, tzinfo=py_timezone.utc))

    def test_fold(self):
        with pytest.raises(ValueError):
            Time.from_py_time(py_time(1, 2, 3, 4, fold=1))


def test_comparison():
    t = Time(1, 2, 3, 4_000)
    same = Time(1, 2, 3, 4_000)
    bigger = Time(2, 2, 3, 4_000)
    smaller = Time(0, 2, 3, 4_000)

    assert t <= same
    assert t <= bigger
    assert not t <= smaller
    assert t <= AlwaysLarger()
    assert not t <= AlwaysSmaller()

    assert not t < same
    assert t < bigger
    assert not t < smaller
    assert t < AlwaysLarger()
    assert not t < AlwaysSmaller()

    assert t >= same
    assert not t >= bigger
    assert t >= smaller
    assert not t >= AlwaysLarger()
    assert t >= AlwaysSmaller()

    assert not t > same
    assert not t > bigger
    assert t > smaller
    assert not t > AlwaysLarger()
    assert t > AlwaysSmaller()


def test_constants():
    assert Time.MIDNIGHT == Time()
    assert Time.NOON == Time(12)
    assert Time.MAX == Time(23, 59, 59, 999_999)


def test_on():
    t = Time(1, 2, 3, 4_000)
    assert t.on(Date(2021, 1, 2)) == NaiveDateTime(2021, 1, 2, 1, 2, 3, 4_000)


def test_pickling():
    t = Time(1, 2, 3, 4_000)
    dumped = pickle.dumps(t)
    assert len(dumped) < len(pickle.dumps(t._py_time)) + 10
    assert pickle.loads(dumped) == t


def test_compatible_unpickle():
    dumped = (
        b"\x80\x04\x95*\x00\x00\x00\x00\x00\x00\x00\x8c\x08whenever\x94\x8c\x0b_unp"
        b"kl_time\x94\x93\x94(K\x01K\x02K\x03M\xa0\x0ft\x94R\x94."
    )
    assert pickle.loads(dumped) == Time(1, 2, 3, 4_000)
