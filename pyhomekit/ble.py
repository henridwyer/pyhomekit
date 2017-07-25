"""Contains all of the HAP-BLE classes."""

import random
import struct

from typing import Tuple

import bluepy.btle

from . import utils
from . import constants


class HapCharacteristic:
    """Represents data or an associated behavior of a service.

    The characteristic is defined by a universally unique type, and has additional
    properties that determine how the value of the characteristic can be accessed.
    """

    def __init__(self, characteristic: bluepy.btle.Characteristic=None):
        self.characteristic = characteristic
        self.peripheral = characteristic.peripheral
        self.cid_descriptor = None
        self.cid = None

    def setup(self, retry=True, max_attempts=2, wait_time=1) -> None:
        """Performs a signature read and reads all characteristic metadata."""
        if retry:
            self.setup_tenacity(max_attempts=max_attempts, wait_time=wait_time)

        self.read_cid()

    def setup_tenacity(self, max_attempts: int, wait_time: int) -> None:
        """Adds automatic retrying to functions that need to read from device."""
        reconnect_callback = utils.reconnect_callback_factory(
            peripheral=self.peripheral)

        retry = utils.reconnect_tenacity_retry(max_attempts, wait_time,
                                               reconnect_callback)

        retry_functions = [self.read_cid, self.signature_read]

        for func in retry_functions:
            print(func, func.__name__)
            name = func.__name__
            setattr(self, name, retry(getattr(self, func.__name__)))

    def read_cid(self):
        """Reads the Characteristic ID, if required."""
        if self.cid is None and self.cid_descriptor is None:
            self.cid_descriptor = self.characteristic.getDescriptors(
                constants.characteristic_ID_descriptor_UUID)[0]
        if self.cid is None:
            self.cid = self.cid_descriptor.read()

    def signature_read(self) -> Tuple[bytes, int]:
        """Reads the signature of the HAP characteristic."""

        # Generate a transaction
        header = HapBlePduRequestHeader(
            cid_sid=self.cid,
            op_code=constants.HapBleOpCodes.Characteristic_Signature_Read, )
        self.characteristic.write(header.data, withResponse=True)
        result = self.characteristic.read()
        return result, header.transation_id

    @staticmethod
    def signature_parse(response: bytes, tid: int) -> None:
        """Parse the signature read response and set attributes."""

        # Check response validity
        control_field = response[0]
        if control_field != 2:
            raise ValueError(
                "Invalid control field {}, expected 2.".format(control_field),
                response)
        if response[1] != tid:
            raise ValueError("Invalid transaction ID {}, expected {}.".format(
                response[1], tid), response)
        status = response[2]
        if status != constants.HapBleStatusCodes.Success:
            raise HapBleError(status_code=status)
        body_length = struct.unpack('<H', response[3:5])[0]
        if len(response[5:]) != body_length:
            raise ValueError("Invalid body length {}, expected {}.".format(
                control_field, body_length), response)

        # Parse remaining data
        for body_type, length, bytes_ in utils.iterate_tvl(response[5:]):
            if len(bytes_) != length:
                raise HapBleError(name="Invalid response length")
            name = constants.HAP_param_type_code_to_name[body_type]
            converter = constants.HAP_param_name_to_converter[name]
            setattr(name, converter(bytes_))


class HapAccessory:
    """Accessory"""

    def __init__(self):
        pass

    def pair(self):
        pass

    def pair_verify(self):
        pass

    def save_key(self):
        pass

    def discover_hap_characteristics(self):
        pass

    def get_characteristic(self, name: str, uuid: str):
        pass


class HapAccessoryLock(HapAccessory):

    # Required
    def lock_current_state(self):
        pass

    # Required
    def lock_target_state(self):
        pass

    # Required for lock management
    def lock_control_point(self):
        pass

    def version(self):
        pass

    # Optional for lock management
    def logs(self):
        pass

    def audio_feedback(self):
        pass

    def lock_management_auto_security_timeout(self):
        pass

    def administrator_only_access(self):
        pass

    def lock_last_known_action(self):
        pass

    def current_door_state(self):
        pass

    def motion_detected(self):
        pass


class HapBlePduRequestHeader:
    """HAP-BLE PDU Header."""

    def __init__(self,
                 cid_sid: bytes,
                 op_code: int,
                 continuation: bool=False,
                 response: bool=False,
                 transation_id: int=None) -> None:
        """HAP-BLE PDU Header.

        Parameters
        ----------
        continuation
            indicates the fragmentation status of the HAP-BLE PDU. False
            indicates a first fragment or no fragmentation.

        request
            indicates whether the PDU is a response (versus a request)

        transation_id
            Transaction Identifier

        op_code
            HAP Opcode field, which indicates the opcode for the HAP Request PDU.

        cid_sid
            Characteristic / Service Instance Identifier is the instance id
            of the characteristic / service for a particular request.
        """
        self.continuation = continuation
        self.response = response
        self.op_code = op_code
        self._transaction_id = transation_id
        self.cid_sid = cid_sid

    @property
    def control_field(self) -> int:
        """Get formatted Control Field."""
        header = "{continuation}00000{response}0".format(
            continuation=int(self.continuation), response=int(self.response))
        return int(header, 2)

    @property
    def transation_id(self) -> int:
        """Get the transaction identifier, or generate a new one if none exists.

        The transation ID is an 8 bit number identifying the transaction
        number of this PDU. The TID is randomly generated by the originator
        of the request and is used to match a request/response pair.
        """
        if self._transaction_id is None:
            self._transaction_id = random.SystemRandom().getrandbits(8)
        return self._transaction_id

    @property
    def data(self) -> bytes:
        """Byte representation of the PDU Header."""
        return struct.pack('<BBB', self.control_field, self.op_code,
                           self.transation_id) + self.cid_sid


class HapBleRequest:
    """HAP-BLE Request."""

    def __init__(self, header: HapBlePduRequestHeader) -> None:
        """HAP-BLE Request.

        header: the header for the request.
        """
        self._header = header

    @property
    def header(self) -> HapBlePduRequestHeader:
        """Get the request header."""
        return self._header


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
