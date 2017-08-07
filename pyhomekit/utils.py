"""Useful functions for pyHomeKit."""

import logging
from struct import pack
from typing import Any, Iterator, Tuple, Union  # NOQA pylint: disable=W0611

from .constants import HAP_param_type_name_to_code

logger = logging.getLogger(__name__)


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


def prepare_tlv(param_type: Union[str, int], value: bytes) -> bytes:
    """Formats the TLV into the expected format of the PDU."""
    if isinstance(param_type, str):
        param_type = HAP_param_type_name_to_code[param_type]
    return pack('<BB', param_type, len(value)) + value
