"""Apple HomeKit encryption helper methods.

The variables in this file follow the names given in the SRP paper:
T. Wu, SRP-6: Improvements and Refinements to the Secure Remote Password Protocol,
Submission to the IEEE P1363 Working Group, Oct 2002.

https://tools.ietf.org/html/rfc5054#ref-SRP-RFC

https://tools.ietf.org/html/rfc2945
"""

from hashlib import sha512
from typing import Union, Dict, Any  # NOQA pylint: disable=W0611

import random
# import libnacl

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
            arg = arg.to_bytes(-(-arg.bit_length() // 8), 'big')
        elif isinstance(arg, str):
            arg = arg.encode('utf-8')
        if pad:
            arg = b'\x00' * (PAD_L - len(arg)) + arg
        byte_args.append(arg)
    return int(sha512(sep.join(byte_args)).hexdigest(), 16)


def random_int(n_bits: int=RANDOM_BITS) -> int:
    """Generates a random int of n bytes, modulo N"""
    return random.SystemRandom().getrandbits(n_bits) % N


k = H(N, g, pad=True)


def pair():
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

    parsed_response = {}
    M2 = parsed_response['kTLVType_Proof']

    M2_calc = H(A, M1, S)
    if M2_calc != M2:
        raise ValueError("Authentication failed - invalid prood received.")
