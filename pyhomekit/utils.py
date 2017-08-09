"""Utility functions for BLE"""

import logging

from struct import pack
from typing import (Any, Callable, Dict, List)  # NOQA pylint: disable=W0611
from typing import (Tuple, Union, Optional, Iterator)  # NOQA pylint: disable=W0611

from . import constants

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


def prepare_tlv(param_type: Union[str, int], value: bytes) -> Iterator[bytes]:
    """Formats the TLV into the expected format of the PDU.

    Parameters
    ----------
    param_type
        The name or code for the HAP Parameter type

    value
        The value in bytes of the parameter.
    """
    if isinstance(param_type, str):
        param_type = constants.HAP_param_type_name_to_code[param_type]
    while value:
        fragment = value[:255]
        yield pack('<BB', param_type, len(fragment)) + fragment
        value = value[255:]

def parse_ktlvs(data: bytes) -> Dict[str, Any]:
    """Parse ktlvs."""
    logger.debug("Parse ktlvs.")
    attributes = {}  # type: Dict[str, Any]
    for body_type, length, bytes_ in iterate_tvl(data):
        if len(bytes_) != length:
            raise HapBleError(name="Invalid response length")
        name = constants.PairingKTlvValues()(body_type)
        attributes[name] = bytes_
        logger.debug("TLV found in response. %s: %s", name, bytes_)

    return attributes


class HapBleError(Exception):
    """HAP Error."""

    def __init__(self,
                 status_code: int=None,
                 name: str=None,
                 message: str=None,
                 *args: str) -> None:
        """HAP Error with appropriate message.

        Parameters
        ----------
        status_code
            the status code of the HAP BLE PDU Response.

        name
            status code name.

        message
            status code message.
        """
        if status_code is None:
            self.name = name
            self.message = message
        else:
            self.status_code = status_code
            self.name = constants.status_code_to_name[status_code]
            self.message = constants.status_code_to_message[status_code]

        super(HapBleError, self).__init__(name, message, *args)

    def __str__(self) -> str:
        """Return formatted error."""
        return "{}: {}".format(self.name, self.message)
