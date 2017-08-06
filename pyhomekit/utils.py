"""Useful functions for pyHomeKit."""

import logging
from struct import pack
from typing import Any, Callable, Iterator, Tuple, Union  # NOQA pylint: disable=W0611

import tenacity

import bluepy.btle

from .constants import HAP_param_type_name_to_code

logger = logging.getLogger(__name__)


def reconnect_callback_factory(
        peripheral: bluepy.btle.Peripheral) -> Callable[[Any, int], None]:
    """Factory for creating tenacity before callbacks to reconnect to a peripheral."""

    # pylint: disable=W0613
    def reconnect(func: Any, trial_number: int) -> None:
        """Attempt to reconnect."""
        try:
            logger.debug("Attempting to reconnect to device.")
            peripheral.connect(peripheral.addr, peripheral.addrType)
        except bluepy.btle.BTLEException:
            logger.debug(
                "Error while attempting to reconnect to device", exc_info=True)

    return reconnect


def reconnect_tenacity_retry(reconnect_callback: Callable[[Any, int], Any],
                             max_attempts: int=2,
                             wait_time: int=2) -> tenacity.Retrying:
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


def prepare_tlv(param_type: Union[str, int], value: bytes) -> bytes:
    """Formats the TLV into the expected format of the PDU."""
    if isinstance(param_type, str):
        param_type = HAP_param_type_name_to_code[param_type]
    return pack('<BB', param_type, len(value)) + value
