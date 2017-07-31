"""Useful functions for pyHomeKit."""

from struct import unpack

from typing import Callable, Any, Tuple, Iterator  # NOQA pylint: disable=W0611

import bluepy.btle
import tenacity


def reconnect_callback_factory(peripheral: bluepy.btle.Peripheral
                               ) -> Callable[[Callable[[Any], Any]], int]:
    """Factory for creating tenacity before callbacks to reconnect to a peripheral."""

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(bluepy.btle.BTLEException),
        stop=tenacity.wait_fixed(2),
        wait=tenacity.stop_after_attempt(2))
    # pylint: disable=W0613
    def reconnect(func: Callable[[Any], Any], trial_number: int) -> None:
        """Attempt to reconnect."""
        peripheral.connect(peripheral.addr)

    return reconnect


def reconnect_tenacity_retry(reconnect_callback: Callable[[Any], Any],
                             max_attempts: int=2,
                             wait_time: int=1) -> tenacity.Retrying:
    """Build tenacity retry object"""
    retry = tenacity.retry(
        stop=tenacity.stop_after_attempt(max_attempts),
        wait=tenacity.wait_fixed(wait_time),
        retry=tenacity.retry_if_exception_type(bluepy.btle.BTLEException),
        before=reconnect_callback)

    return retry


def iterate_tvl(response: bytes) -> Iterator[Tuple[int, int, bytes]]:
    """Iterate through response bytes, 1 tlv at a time."""
    start = 0
    end = 0
    while end < len(response):
        # First byte indidates type
        body_type = response[start]
        # Next byte indicates length
        length = response[start + 1]
        yield body_type, length, response[start + 2:start + 2 + length]
        start += 2 + length
        end += 2 + length


def to_uuid(b: bytes) -> str:
    """Convert bytes to string representation of uuid.

    The bytes are reversed first."""
    s = b[::-1].hex()
    return '-'.join((s[:8], s[8:12], s[12:16], s[16:20], s[20:]))


def to_bool(b: bytes) -> bool:
    """Convert to bytes to bool (little endian)."""
    return unpack('<?', b)[0]


def to_float(b: bytes) -> int:
    """Convert to bytes to float (little endian)."""
    return unpack('<f', b)[0]


def to_int32(b: bytes) -> int:
    """Convert to bytes to 32 bit signed int (little endian)."""
    return unpack('<i', b)[0]


def to_uint64(b: bytes) -> int:
    """Convert to bytes to 64 bit unsigned int (little endian)."""
    return unpack('<Q', b)[0]


def to_uint32(b: bytes) -> int:
    """Convert to bytes to 32 bit unsigned int (little endian)."""
    return unpack('<I', b)[0]


def to_uint16(b: bytes) -> int:
    """Convert to bytes to 16 bit unsigned short (little endian)."""
    return unpack('<H', b)[0]


def to_uint8(b: bytes) -> int:
    """Convert to bytes to 8 bit unsigned short (little endian)."""
    return unpack('<B', b)[0]


def to_utf8(b: bytes) -> str:
    """Convert bytes to str utf-8 encoded."""
    return b.decode('utf-8')


def parse_format(b: bytes) -> Tuple[int, int]:
    """Parse the bluetooth characteristic presentation format to format and unit code"""
    format_ = unpack('<B', b[0:1])[0]
    exponent = unpack('<b', b[1:2])[0]  # Not used, should be 0
    unit = unpack('<H', b[2:4])[0]
    namespace = unpack('<b', b[4:5])[0]  # Not used, should be 1
    description = unpack('<H', b[5:])[0]  # Not used, should be 0

    if exponent != 0 or namespace != 1 or description != 0:
        raise ValueError("Unexpected presentation format: {}".format(b))

    return (format_, unit)


def identity(x: Any) -> Any:
    """Identity"""
    return x
