"""Apple HomeKit encryption helper methods.

The variables in this file follow the names given in the SRP paper:
T. Wu, SRP-6: Improvements and Refinements to the Secure Remote Password Protocol,
Submission to the IEEE P1363 Working Group, Oct 2002.

https://tools.ietf.org/html/rfc5054#ref-SRP-RFC

https://tools.ietf.org/html/rfc2945
"""

import logging
import os
import random

from hashlib import sha512
from struct import pack
from typing import Any, Dict, List, Tuple, Union, Optional  # NOQA pylint: disable=W0611

import cryptography.hazmat
from libnacl import (crypto_aead_chacha20poly1305_ietf_decrypt,
                     crypto_aead_chacha20poly1305_ietf_encrypt)

import ed25519

from . import constants, utils

logger = logging.getLogger(__name__)

# Constants
N_HEX = """FFFFFFFF FFFFFFFF C90FDAA2 2168C234 C4C6628B 80DC1CD1 29024E08
           8A67CC74 020BBEA6 3B139B22 514A0879 8E3404DD EF9519B3 CD3A431B
           302B0A6D F25F1437 4FE1356D 6D51C245 E485B576 625E7EC6 F44C42E9
           A637ED6B 0BFF5CB6 F406B7ED EE386BFB 5A899FA5 AE9F2411 7C4B1FE6
           49286651 ECE45B3D C2007CB8 A163BF05 98DA4836 1C55D39A 69163FA8
           FD24CF5F 83655D23 DCA3AD96 1C62F356 208552BB 9ED52907 7096966D
           670C354E 4ABC9804 F1746C08 CA18217C 32905E46 2E36CE3B E39E772C
           180E8603 9B2783A2 EC07A28F B5C55DF0 6F4C52C9 DE2BCBF6 95581718
           3995497C EA956AE5 15D22618 98FA0510 15728E5A 8AAAC42D AD33170D
           04507A33 A85521AB DF1CBA64 ECFB8504 58DBEF0A 8AEA7157 5D060C7D
           B3970F85 A6E1E4C7 ABF5AE8C DB0933D7 1E8C94E0 4A25619D CEE3D226
           1AD2EE6B F12FFA06 D98A0864 D8760273 3EC86A64 521F2B18 177B200C
           BBE11757 7A615D6C 770988C0 BAD946E2 08E24FA0 74E5AB31 43DB5BFC
           E0FD108E 4B82D120 A93AD2CA FFFFFFFF FFFFFFFF"""
N = int(''.join(N_HEX.split()), 16)
PAD_L = N.bit_length() // 8
g = 5

USERNAME = 'Pair-Setup'

SALT_BITS = 64
RANDOM_BITS = 512
password = ''


def H(*args: Union[int, bytes, str], sep: bytes=b'', pad: bool=False) -> int:
    """Hash concatenated arguments"""
    # convert to bytes if necessary
    byte_args = []
    for arg in args:
        if isinstance(arg, int):
            arg = to_bytes(arg, False)
        elif isinstance(arg, str):
            arg = arg.encode('utf-8')
        if pad:
            arg = b'\x00' * (PAD_L - len(arg)) + arg
        byte_args.append(arg)
    return int(sha512(sep.join(byte_args)).hexdigest(), 16)


def random_int(n_bits: int=RANDOM_BITS) -> int:
    """Generates a random int of n bytes, modulo N"""
    return random.SystemRandom().getrandbits(n_bits) % N


def to_bytes(value: int, little_endian: bool=True) -> bytes:
    """Transforms the int into bytes."""
    if little_endian:
        order = 'little'
    else:
        order = 'big'
    return value.to_bytes(-(-value.bit_length() // 8), order)


def from_bytes(value: bytes, little_endian: bool=True) -> int:
    """Transform bytes representation of int into an int."""
    value_hex = value.hex()
    if little_endian:
        value_hex = value_hex[::-1]
    return int(value_hex, 16)


k = H(N, g, pad=True)


def derive_session_key(shared_secret: bytes,
                       salt: bytes=b"Pair-Setup-Controller-Sign-Salt",
                       info: bytes=b"Pair-Setup-Controller-Sign-Info",
                       output_size: int=32) -> bytes:
    """Derive X from the SRP shared secret by using HKDF-SHA-512."""
    hkdf = cryptography.hazmat.primitives.kdf.hkdf.HKDF(
        algorithm=cryptography.hazmat.primitives.hashes.SHA512(),
        length=output_size,
        salt=salt,
        info=info,
        backend=cryptography.hazmat.backends.default_backend())
    return hkdf.derive(to_bytes(shared_secret))


class SRPPairSetup:
    """Secure Remote Protocol session for pair setup.

    This class is used to generate messages for pairing using SRP
    and generates the long term cryptographic keys.

    Parameters
    ----------
    pairing_id
        Unique identifier for the controller. Must be formatted as
        XX:XX:XX:XX:XX:XX", where "XX" is a hexadecimal string representing a byte.

    setup_code
        Code for the pairing, Must be formatted as
        XXX-XX-XXX where each X is a 0-9 digit and dashes are required.
        This code can be passed when creating the session, or after
        starting the pairing (for m3).

    storage_folder
        Folder path to store the pairing keys.
        This folder should be secure to prevent unauthorized access.
    """

    def __init__(self,
                 pairing_id: bytes,
                 setup_code: str=None,
                 storage_folder: str=None) -> None:
        self.setup_code = setup_code
        self.pairing_id = pairing_id
        self.storage_folder = storage_folder

        self.g = g
        self.N = N
        self.k = H(self.N, self.g, pad=True)
        self.B = 0  # type: int
        self.s = 0  # type: int
        self.my_s = 0  # type: int
        self.x = 0  # type: int
        self.a = 0  # type: int
        self.A = 0  # type: int
        self.u = 0  # type: int
        self.S = 0  # type: int
        self.K = 0  # type: int
        self.M1 = 0  # type: int
        self.M2 = 0  # type: int
        self.X = 0  # type: int
        self.state = 0
        self.signing_key = None  # type: Optional[ed25519.SigningKey]
        self.verifying_key = None  # type: Optional[ed25519.VerifyingKey]
        self.device_info = b''  # type: bytes
        self.device_signature = b''  # type: bytes
        self.accessory_pairing_id = b''  # type: bytes
        self.accessory_ltpk = b''  # type: bytes
        self.accessory_signature = b''  # type: bytes

    @staticmethod
    def m1_generate_srp_start_request() -> List[Tuple[int, bytes]]:
        """Generate the SRP Start request message TLVs.

        The message contains 2 TLVs:
        - Return_Response: 1
        - Vale: kTLVs

        With the kTLVs:
        - kTLVType_State <M1>
        - kTLVType_Method <Pair Setup>
        """
        ktlvs = [(constants.PairingKTlvValues.kTLVType_State, pack('<B', 1)),
                 (constants.PairingKTlvValues.kTLVType_Method, pack(
                     '<B', constants.PairingKTLVMethodValues.Pair_Setup))]

        prepared_ktlvs = b''.join(
            data for ktlv in ktlvs for data in utils.prepare_tlv(*ktlv))

        message_data = [(constants.HapParamTypes.Return_Response, pack(
            '<B', 1)), (constants.HapParamTypes.Value, prepared_ktlvs)]

        return message_data

    def m2_receive_srp_start_response(self,
                                      parsed_ktlvs: Dict[str, bytes]) -> None:
        """Update SRP session with m2 response"""
        if from_bytes(parsed_ktlvs['kTLVType_State']) != 2:
            raise ValueError(
                "Received wrong message for M2 {}".format(parsed_ktlvs))
        self.B = from_bytes(parsed_ktlvs['kTLVType_PublicKey'])
        self.s = from_bytes(parsed_ktlvs['kTLVType_Salt'])

        if self.B >= N or self.B <= 0:
            raise ValueError("Invalid public key received")

    def m3_generate_srp_verify_request(
            self, setup_code: str=None) -> List[Tuple[int, bytes]]:
        """Generate the SRP Verify request message TLVs.

        The message contains 2 TLVs:
        - Return_Response: 1
        - Vale: kTLVs

        With the kTLVs:
        - kTLVType_State <M3>
        - kTLVType_PublicKey <iOS device's SRP public key> - A
        - kTLVType_Proof <iOS device's SRP proof> - M1
        """
        if self.setup_code is None:
            self.setup_code = setup_code
        if self.setup_code is None:
            raise ValueError("No setup code, cannot proceed with M3")
        self.x = H(self.s, H(USERNAME, self.setup_code, sep=b":"))
        self.a = random_int(RANDOM_BITS)
        self.A = pow(self.g, self.a, self.N)

        self.u = H(self.A, self.B, pad=True)
        self.S = pow(self.B - (self.k * pow(self.g, self.x, self.N)),
                     self.a + (self.u * self.x), self.N)
        self.K = H(self.S)
        # self.M1 = H(self.A, self.B, self.S)
        self.M1 = H(H(N) ^ H(g), H(USERNAME), self.s, self.A, self.B, self.K)

        ktlvs = [(constants.PairingKTlvValues.kTLVType_State, pack('<B', 3)),
                 (constants.PairingKTlvValues.kTLVType_PublicKey,
                  to_bytes(self.A)),
                 (constants.PairingKTlvValues.kTLVType_Proof,
                  to_bytes(self.M1))]

        prepared_ktlvs = b''.join(
            data for ktlv in ktlvs for data in utils.prepare_tlv(*ktlv))

        message_data = [(constants.HapParamTypes.Return_Response, pack(
            '<B', 1)), (constants.HapParamTypes.Value, prepared_ktlvs)]

        return message_data

    def m4_receive_srp_verify_response(self,
                                       parsed_ktlvs: Dict[str, bytes]) -> None:
        """Verify accessory's proof."""
        if parsed_ktlvs['kTLVType_State'] != 4:
            raise ValueError(
                "Received wrong message for M4 {}".format(parsed_ktlvs))
        self.M2 = from_bytes(parsed_ktlvs['kTLVType_Proof'])

        M2_calc = H(self.A, self.M1, self.K)
        if M2_calc != self.M2:
            raise ValueError("Authentication failed - invalid prood received.")

    def m5_generate_exchange_request(self) -> List[Tuple[int, bytes]]:
        """Generate the Request Generation, as well as signing and encryption keys.

        The message contains 2 TLVs:
        - Return_Response: 1
        - Vale: kTLVs

        With the kTLVs:
        - kTLVType_State <M5>
        - kTLVType_EncryptedData <encryptedData with authTag appended>

        The encrypted data contains the ktlvs:
        - kTLVType_Identifier <iOSDevicePairingID>
        - kTLVType_PublicKey <iOSDeviceLTPK> - verifying_key
        - kTLVType_Signature <iOSDeviceSignature>
        """
        # 1. Generate Ed25519 long-term public key, iOSDeviceLTPK,
        # and long-term secret key, iOSDeviceLTSK
        if self.signing_key is None:
            self.signing_key, _ = ed25519.create_keypair()
            with open(os.path.join(self.storage_folder, "secret-key"),
                      "wb") as secret_key_file:
                secret_key_file.write(self.signing_key.to_bytes())
        self.verifying_key = self.signing_key.get_verifying_key()

        # 2. Derive iOSDeviceX from the SRP shared secret by using HKDF-SHA-512
        salt = b"Pair-Setup-Controller-Sign-Salt"
        info = b"Pair-Setup-Controller-Sign-Info"
        output_size = 32

        hkdf = cryptography.hazmat.primitives.kdf.hkdf.HKDF(
            algorithm=cryptography.hazmat.primitives.hashes.SHA512(),
            length=output_size,
            salt=salt,
            info=info,
            backend=cryptography.hazmat.backends.default_backend())
        self.X = hkdf.derive(to_bytes(self.S))

        # 3. Concatenate iOSDeviceX with the iOS device's Pairing Identifier, iOSDevicePairingID,
        # and its long-term public key, iOSDeviceLTPK.
        # The concatenated value will be referred to as iOSDeviceInfo.

        self.device_info = (
            to_bytes(self.X) + self.pairing_id + self.verifying_key.to_bytes())

        # 4. Generate iOSDeviceSignature by signing iOSDeviceInfo with its
        # long-term secret key, iOSDeviceLTSK, using Ed25519.

        self.device_signature = self.signing_key.sign(self.device_info)

        # 5. Construct a sub-TLV
        sub_ktlvs = [(constants.PairingKTlvValues.kTLVType_Identifier,
                      self.pairing_id),
                     (constants.PairingKTlvValues.kTLVType_PublicKey,
                      self.verifying_key.to_bytes()),
                     (constants.PairingKTlvValues.kTLVType_Signature,
                      self.device_signature)]

        prepared_sub_ktlvs = b''.join(
            data for ktlv in sub_ktlvs for data in utils.prepare_tlv(*ktlv))

        # 6. Encrypt the sub-TLV, encryptedData, and generate the 16 byte auth tag, authTag.
        # using the ChaCha20-Poly1305 AEAD algorithm

        # this includes the auth_tag appended at the end
        encrypted_data = crypto_aead_chacha20poly1305_ietf_encrypt(
            key=self.S, nonce="PS-Msg05", aad=None, message=prepared_sub_ktlvs)

        ktlvs = [(constants.PairingKTlvValues.kTLVType_State, pack('<B', 5)),
                 (constants.PairingKTlvValues.kTLVType_EncryptedData,
                  encrypted_data)]

        # 7. Build request data
        prepared_ktlvs = b''.join(
            data for ktlv in ktlvs for data in utils.prepare_tlv(*ktlv))

        message_data = [(constants.HapParamTypes.Return_Response, pack(
            '<B', 5)), (constants.HapParamTypes.Value, prepared_ktlvs)]

        return message_data

    def m6_receive_exchange_response(self,
                                     parsed_ktlvs: Dict[str, int]) -> None:
        """Verify accessory and save pairing."""
        if parsed_ktlvs['kTLVType_State'] != 6:
            raise ValueError(
                "Received wrong message for M6 {}".format(parsed_ktlvs))

        decrypted_ktlvs = crypto_aead_chacha20poly1305_ietf_decrypt(
            parsed_ktlvs['kTLVType_EncryptedData'],
            nonce=b"PS-Msg06",
            aad=None,
            key=self.S)

        parsed_decrypted_ktlvs = utils.parse_ktlvs(decrypted_ktlvs)

        self.accessory_pairing_id = parsed_decrypted_ktlvs[
            'kTLVType_Identifier']
        self.accessory_ltpk = parsed_decrypted_ktlvs['kTLVType_PublicKey']
        self.accessory_signature = parsed_decrypted_ktlvs['kTLVType_Signature']

        with open(
                os.path.join(self.storage_folder, "accessory_pairing_id"),
                "wb") as accessory_pairing_id_file:
            accessory_pairing_id_file.write(self.accessory_pairing_id)
        with open(os.path.join(self.storage_folder, "accessory_ltpk"),
                  "wb") as accessory_ltpk_file:
            accessory_ltpk_file.write(self.accessory_ltpk)

        logger.debug(
            "Successfully saved accessory pairing id and accessory long term public key"
        )


class SRPPairVerify:
    """Secure Remote Protocol session for pair verify.

    You must already have paired with an accessory.

    Parameters
    ----------
    pairing_id
        Unique identifier for the controller. Must be formatted as
        XX:XX:XX:XX:XX:XX", where "XX" is a hexadecimal string representing a byte.

    setup_code
        Code for the pairing, Must be formatted as
        XXX-XX-XXX where each X is a 0-9 digit and dashes are required.
        This code can be passed when creating the session, or after
        starting the pairing (for m3).

    storage_folder
        Folder path to store the pairing keys.
        This folder should be secure to prevent unauthorized access.
    """

    def __init__(self,
                 pairing_id: bytes,
                 setup_code: str=None,
                 storage_folder: str=None) -> None:
        self.setup_code = setup_code
        self.pairing_id = pairing_id
        self.storage_folder = storage_folder

        self.signing_key = None  # type: Optional[ed25519.SigningKey]
        self.verifying_key = None  # type: Optional[ed25519.VerifyingKey]
        self.device_info = b''  # type: bytes
        self.device_signature = b''  # type: bytes
        self.accessory_pairing_id = b''  # type: bytes
        self.accessory_ltpk = b''  # type: bytes
        self.accessory_signature = b''  # type: bytes

    def m1_generate_verify_start_request(self) -> List[Tuple[int, bytes]]:
        """Generate the SRP Start request message TLVs.

        The message contains 2 TLVs:
        - Return_Response: 1
        - Vale: kTLVs

        With the kTLVs:
        - kTLVType_State <M1>
        - kTLVType_PublicKey <Curve25519 public key>
        """
        with open(os.path.join(self.storage_folder, "secret-key"),
                  "rb") as secret_key_file:
            self.secret_key = ed25519.SigningKey(secret_key_file.read())
        self.verifying_key = self.secret_key.get_verifying_key()

        ktlvs = [(constants.PairingKTlvValues.kTLVType_State, pack('<B', 1)),
                 (constants.PairingKTlvValues.kTLVType_PublicKey,
                  self.verifying_key.to_bytes())]

        prepared_ktlvs = b''.join(
            data for ktlv in ktlvs for data in utils.prepare_tlv(*ktlv))

        message_data = [(constants.HapParamTypes.Return_Response, pack(
            '<B', 1)), (constants.HapParamTypes.Value, prepared_ktlvs)]

        return message_data

    def m2_receive_start_response(self,
                                  parsed_ktlvs: Dict[str, bytes]) -> None:
        """Update SRP session with m2 response"""
        if from_bytes(parsed_ktlvs['kTLVType_State']) != 2:
            raise ValueError(
                "Received wrong message for M2 {}".format(parsed_ktlvs))
        proof = from_bytes(parsed_ktlvs['kTLVType_PublicKey'])
        encrypted_data = from_bytes(parsed_ktlvs['kTLVType_EncryptedData'])

        if proof == encrypted_data:
            print("")


def pair() -> None:
    """Pairing SRP protocol"""
    # Protocol Summary

    # Message 1: Send to accessory
    # SRP Start Request
    # kTLVType_State <M1>
    # kTLVType_Method <Pair Setup>

    # Message 2: Receive from accessory
    # SRP Start Response
    # kTLVType_State <M2>
    # kTLVType_PublicKey <Accessory's SRP public key> - s
    # kTLVType_Salt <16 byte salt generated in Step 6>  - B
    parsed_response = {}  # type: Dict[str, Any]
    B = parsed_response['kTLVType_PublicKey']
    s = parsed_response['kTLVType_Salt']

    # Message 3: Send to accessory
    # SRP Verify Request
    # kTLVType_State <M3>
    # kTLVType_PublicKey <iOS device's SRP public key> - A
    # kTLVType_Proof <iOS device's SRP proof> - M1
    my_s = random_int(SALT_BITS)
    x = H(my_s, H(USERNAME, password, sep=b":"))
    a = random_int(RANDOM_BITS)
    A = pow(g, a, N)

    u = H(A, B, pad=True)
    S = pow(B - (k * pow(g, x, N)), a + (u * x), N)
    K = H(S)
    M1 = H(A, B, S)
    # M1 = H(H(N) | H(g), H(USERNAME), s, A, B, K)

    # Message 4: Receive from accessory
    # SRP Verify Response
    # kTLVType_State <M4>
    # kTLVType_Proof <Accessory's SRP proof> - M2

    parsed_response = {s: K}
    M2 = parsed_response['kTLVType_Proof']

    M2_calc = H(A, M1, K)
    if M2_calc != M2:
        raise ValueError("Authentication failed - invalid prood received.")

    # Message 5: Send to accessory
    # Request Generation

    # kTLVType_State <M5>
    # kTLVType_EncryptedData <encryptedData with authTag appended>

    # The encrypted data contains
    # kTLVType_Identifier  <iOSDevicePairingID>
    # kTLVType_PublicKey <iOSDeviceLTPK>
    # kTLVType_Signature <iOSDeviceSignature>

    # signing_key, verifying_key = ed25519.create_keypair()

    # # Derive iOSDeviceX
    # clientX = ''
    # InputKey = S
    # Salt = b"Pair-Setup-Controller-Sign-Salt"
    # Info = b"Pair-Setup-Controller-Sign-Info"
    # OutputSize = 32
