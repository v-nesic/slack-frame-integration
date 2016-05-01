from base64 import encodestring
from base64 import decodestring
from Crypto.Cipher import AES
from Crypto import Random
from urllib import quote_plus
from urllib import unquote_plus


class FrameCypher:
    key = ''

    def __init__(self, key='Ilf9DroMDs5kUS0fPo5z2g=='):
        self.key = key

    def encrypt(self, message):
        iv = Random.new().read(AES.block_size)
        return quote_plus(encodestring(iv + AES.new(self.key, AES.MODE_CFB, iv).encrypt(message)))

    def decrypt(self, message):
        decoded_message = decodestring(unquote_plus(message))
        iv = decoded_message[:AES.block_size]
        return AES.new(self.key, AES.MODE_CFB, iv).decrypt(decoded_message[AES.block_size:])


