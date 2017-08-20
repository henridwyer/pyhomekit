"""HAP Constants"""

from struct import unpack
from typing import Dict, Any, Optional, Tuple  # NOQA pylint: disable=W0611


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


def identity(x: Any) -> Any:
    """Identity"""
    return x


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


characteristic_ID_descriptor_UUID = 'DC46F0FE-81D2-4616-B5D9-6ABDD796939A'
pairing_service_UUID = "00000055-0000-1000-8000-0026BB765291"
pair_setup_characteristic_UUID = "0000004C-0000-1000-8000-0026BB765291"
pair_verify_characteristic_UUID = "0000004E-0000-1000-8000-0026BB765291"
pairing_features_characteristic_UUID = "0000004F-0000-1000-8000-0026BB765291"


class HapParamTypes:
    Value = 1
    Additional_Authorization_Data = 2
    Origin_local_vs_remote = 3
    Characteristic_Type = 4
    Characteristic_Instance_ID = 5
    Service_Type = 6
    Service_Instance_ID = 7
    TTL = 8
    Return_Response = 9
    HAP_Characteristic_Properties_Descriptor = 10
    GATT_User_Description_Descriptor = 11
    GATT_Presentation_Format_Descriptor = 12
    GATT_Valid_Range = 13
    HAP_Step_Value_Descriptor = 14
    HAP_Service_Properties = 15
    HAP_Linked_Services = 16
    HAP_Valid_Values_Descriptor = 17
    HAP_Valid_Values_Range_Descriptor = 18

    def __call__(self, code: int) -> str:
        return HAP_param_type_code_to_name[code]


HAP_param_type_code_to_name = {
    1: 'Value',
    2: 'Additional_Authorization_Data',
    3: 'Origin_local_vs_remote',
    4: 'Characteristic_Type',
    5: 'Characteristic_Instance_ID',
    6: 'Service_Type',
    7: 'Service_Instance_ID',
    8: 'TTL',
    9: 'Return_Response',
    10: 'HAP_Characteristic_Properties_Descriptor',
    11: 'GATT_User_Description_Descriptor',
    12: 'GATT_Presentation_Format_Descriptor',
    13: 'GATT_Valid_Range',
    14: 'HAP_Step_Value_Descriptor',
    15: 'HAP_Service_Properties',
    16: 'HAP_Linked_Services',
    17: 'HAP_Valid_Values_Descriptor',
    18: 'HAP_Valid_Values_Range_Descriptor'
}

HAP_param_type_name_to_code = {
    "Value": 1,
    "Additional_Authorization_Data": 2,
    "Origin_local_vs_remote": 3,
    "Characteristic_Type": 4,
    "Characteristic_Instance_ID": 5,
    "Service_Type": 6,
    "Service_Instance_ID": 7,
    "TTL": 8,
    "Return_Response": 9,
    "HAP_Characteristic_Properties_Descriptor": 10,
    "GATT_User_Description_Descriptor": 11,
    "GATT_Presentation_Format_Descriptor": 12,
    "GATT_Valid_Range": 13,
    "HAP_Step_Value_Descriptor": 14,
    "HAP_Service_Properties": 15,
    "HAP_Linked_Services": 16,
    "HAP_Valid_Values_Descriptor": 17,
    "HAP_Valid_Values_Range_Descriptor": 18
}

HAP_param_code_to_converter = {
    1: identity,
    2: identity,
    3: identity,
    4: to_uuid,
    5: to_uuid,
    # DC46F0FE-81D2-4616-B5D9-6ABDD796939A
    6: to_uuid,
    7: to_uint16,
    # E604E95D-A759-4817-87D3-AA005083A0D1
    8: identity,
    9: identity,
    10: to_uint16,
    11: to_utf8,
    12: parse_format,
    13: identity,
    14: identity,
    15: to_uint16,
    16: identity,
    17: identity,
    18: identity
}  # type: Dict[int, Any]

HAP_param_name_to_converter = {
    "Value": identity,
    "Additional_Authorization_Data": identity,
    "Origin_local_vs_remote": identity,
    "Characteristic_Type": to_uuid,
    "Characteristic_Instance_ID": to_uuid,
    # DC46F0FE-81D2-4616-B5D9-6ABDD796939A
    "Service_Type": to_uuid,
    "Service_Instance_ID": to_uint16,
    # E604E95D-A759-4817-87D3-AA005083A0D1
    "TTL": identity,
    "Return_Response": identity,
    "HAP_Characteristic_Properties_Descriptor": to_uint16,
    "GATT_User_Description_Descriptor": to_utf8,
    "GATT_Presentation_Format_Descriptor": parse_format,
    "GATT_Valid_Range": identity,
    "HAP_Step_Value_Descriptor": identity,
    "HAP_Service_Properties": to_uint16,
    "HAP_Linked_Services": identity,
    "HAP_Valid_Values_Descriptor": identity,
    "HAP_Valid_Values_Range_Descriptor": identity
}  # type: Dict[str, Any]

format_code_to_name = {
    0x01: 'bool',
    0x04: 'uint8',
    0x06: 'unit16',
    0x08: 'uint32',
    0x0A: 'uint64',
    0x10: 'int',
    0x14: 'float',
    0x19: 'string',
    0x1B: 'data'
}

format_name_to_converter = {
    'bool': to_bool,
    'uint8': to_uint8,
    'uint16': to_uint16,
    'uint32': to_uint32,
    'uint64': to_uint64,
    'int': to_int32,
    'float': to_float,
    'string': to_utf8,
    'data': lambda x: x
}

unit_name_to_code = {
    'celsius': 0x272F,
    'arcdegrees': 0x2763,
    'percentage': 0x27AD,
    'unitless': 0x2700,
    'lux': 0x2731,
    'seconds': 0x2703
}

unit_code_to_name = {
    9984: 'unitless',
    9987: 'seconds',
    10031: 'celsius',
    10033: 'lux',
    10083: 'arcdegrees',
    10157: 'percentage'
}

pairing_tlv_value_to_name = {
    0: 'kTLVType_Method',
    1: 'kTLVType_Identifier',
    2: 'kTLVType_Salt',
    3: 'kTLVType_PublicKey',
    4: 'kTLVType_Proof',
    5: 'kTLVType_EncryptedData',
    6: 'kTLVType_State',
    7: 'kTLVType_Error',
    8: 'kTLVType_RetryDelay',
    9: 'kTLVType_Certificate',
    10: 'kTLVType_Signature',
    11: 'kTLVType_Permissions',
    12: 'kTLVType_FragmentData',
    13: 'kTLVType_FragmentLast',
    255: 'kTLVType_Separator'
}

pairing_tlv_name_to_format = {
    'kTLVType_Certificate': 'bytes',
    'kTLVType_EncryptedData': 'bytes',
    'kTLVType_Error': 'integer',
    'kTLVType_FragmentData': 'bytes',
    'kTLVType_FragmentLast': 'bytes',
    'kTLVType_Identifier': 'UTF-8',
    'kTLVType_Method': 'integer',
    'kTLVType_Permissions': 'integer',
    'kTLVType_Proof': 'bytes',
    'kTLVType_PublicKey': 'bytes',
    'kTLVType_RetryDelay': 'integer',
    'kTLVType_Salt': 'bytes',
    'kTLVType_Separator': 'null',
    'kTLVType_Signature': 'bytes',
    'kTLVType_State': 'integer'
}

pairing_ktlv_method_value_code_to_name = {
    0: "Reserved",
    1: "Pair_Setup",
    2: "Pair_Verify",
    3: "Add_Pairing",
    4: "Remove_Pairing",
    5: "List_Pairings"
}

pairing_ktlv_error_code_to_name = {
    0: 'n/a',
    1: 'kTLVError_Unknown',
    2: 'kTLVError_Authentication',
    3: 'kTLVError_Backoff',
    4: 'kTLVError_MaxPeers',
    5: 'kTLVError_MaxTries',
    6: 'kTLVError_Unavailable',
    7: 'kTLVError_Busy'
}


class PairingKTLVErrorCodes:
    kTLVError_Unknow = 0x01
    kTLVError_Authenticatio = 0x02
    kTLVError_Backof = 0x03
    kTLVError_MaxPeer = 0x04
    kTLVError_MaxTrie = 0x05
    kTLVError_Unavailabl = 0x06
    kTLVError_Bus = 0x07

    def __call__(self, code: int) -> str:
        return pairing_ktlv_error_code_to_name[code]


class PairingKTlvValues:
    """Pairng service TLV Values."""
    kTLVType_Method = 0x00
    kTLVType_Identifier = 0x01
    kTLVType_Salt = 0x02
    kTLVType_PublicKey = 0x03
    kTLVType_Proof = 0x04
    kTLVType_EncryptedData = 0x05
    kTLVType_State = 0x06
    kTLVType_Error = 0x07
    kTLVType_RetryDelay = 0x08
    kTLVType_Certificate = 0x09
    kTLVType_Signature = 0x0A
    kTLVType_Permissions = 0x0B
    kTLVType_FragmentData = 0x0C
    kTLVType_FragmentLast = 0x0D
    kTLVType_Separator = 0xFF

    def __call__(self, code: int) -> str:
        return pairing_tlv_value_to_name[code]


class PairingKTLVMethodValues:
    """Pairing service kTLV method values"""
    Reserved = 0
    Pair_Setup = 1
    Pair_Verify = 2
    Add_Pairing = 3
    Remove_Pairing = 4
    List_Pairings = 5

    def __call__(self, code: int) -> str:
        """Return the kTLV Type Method value name."""
        return pairing_ktlv_method_value_code_to_name[code]


class HapBleStatusCodes:
    """HAP Status code definitions and descriptions."""

    Success = 0x00
    Unsupported_PDU = 0x01
    Max_Procedures = 0x02
    Insufficient_Authorization = 0x03
    Invalid_Instance_ID = 0x04
    Insufficient_Authentication = 0x05
    Invalid_Request = 0x06

    def __call__(self, code: int) -> str:
        """Return the status code name."""
        return status_code_to_name[code]


class HapBleOpCodes:
    """HAP Opcode Descriptions."""

    Characteristic_Signature_Read = 0x01
    Characteristic_Write = 0x02
    Characteristic_Read = 0x03
    Characteristic_Timed_Write = 0x04
    Characteristic_Execute_Write = 0x05
    Service_Signature_Read = 0x06

    def __call__(self, code: int) -> str:
        """Return the op code name."""
        return op_code_to_name[code]


op_code_to_name = {
    1: 'Characteristic_Signature_Read',
    2: 'Characteristic_Write',
    3: 'Characteristic_Read',
    4: 'Characteristic_Timed_Write',
    5: 'Characteristic_Execute_Write',
    6: 'Service_Signature_Read'
}

status_code_to_name = {
    0: 'Success',
    1: 'Unsupported_PDU',
    2: 'Max_Procedures',
    3: 'Insufficient Authorization',
    4: 'Invalid Instance ID',
    5: 'Insufficient Authentication',
    6: 'Invalid Request'
}

status_code_to_message = {
    0x00:
    'The request was successful.',
    0x01:
    'The request failed as the HAP PDU was not recognized or supported.',
    0x02:
    'The request failed as the accessory has reached the the limit on the '
    'simultaneous procedures it can handle.',
    0x03:
    'Characteristic requires additional authorization data.',
    0x04:
    "The HAP Request's characteristic Instance id did not match the addressed "
    "characteristic's instance id.",
    0x05:
    'Characteristic access required a secure session to be established.',
    0x06:
    'Accessory was not able to perform the requested operation.'
}
