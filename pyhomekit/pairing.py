"""Apple HomeKit encryption helper methods."""

import srp
import libnacl

from hashlib import sha512
hash_ = sha512

# SRP Start request

kTLVType_State <M1>
kTLVType_Method <Pair Setup>


# accessory
SRP username 'Pair-Setup'

code

public_key = srp_gen_pub

response:
kTLVType_State <M2>
kTLVType_PublicKey <Accessory's SRP public key>
kTLVType_Salt <16 byte salt generated in Step 6> 

accessory_salt, accessory_key = srp.create_salted_verification_key(username, password)
srp_user = srp.User(username, setup_code)
uname, accessory_public_key = srp_user.start_authentication()

# Send accessory_salt, accessory_public_key

# SRP Verify Request

# verify kTLVType_Error not present
username = 'Pair-Setup'
accessory_salt = parsed_response['kTLVType_Salt']
A = parsed_response['kTLVType_PublicKey']
password = code

controller_salt, controller_key = srp.create_salted_verification_key(username, password)


srp_usr = srp.User(srp_username, setup_code)
uname, A = usr.start_authentication()

verifier = srp.Verifier(username, salt, vkey,  )
_, challenge      = verifier.get_challenge()


to send:
kTLVType_State <M3>
kTLVType_PublicKey <iOS device's SRP public key>
kTLVType_Proof <iOS device's SRP proof>


