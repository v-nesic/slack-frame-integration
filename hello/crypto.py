from base64 import urlsafe_b64encode
from base64 import urlsafe_b64decode
from Crypto.Cipher import AES
from Crypto import Random


class FrameCypher:
    def __init__(self, key='Ilf9DroMDs5kUS0fPo5z2g=='):
        self.key = key

    def encrypt(self, message):
        iv = Random.new().read(AES.block_size)
        return urlsafe_b64encode(iv + AES.new(self.key, AES.MODE_CFB, iv).encrypt(message)).rstrip('=')

    def decrypt(self, message):
        decoded_message = urlsafe_b64decode(message.encode("utf-8") + '===')
        iv = decoded_message[:AES.block_size]
        return AES.new(self.key, AES.MODE_CFB, iv).decrypt(decoded_message[AES.block_size:])
