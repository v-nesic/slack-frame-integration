import json
from base64 import urlsafe_b64encode, urlsafe_b64decode
from Crypto import Random
from Crypto.Cipher import AES


class FrameCypherException(Exception):
    pass


class FrameCypherMessageInvalidToken(FrameCypherException):
    def __init__(self, message=''):
        super(FrameCypherMessageInvalidToken, self).__init__('FrameCypherMessageInvalidToken: {}'.format(message))


class FrameCypherMessageTooShortError(FrameCypherException):
    def __init__(self, message=''):
        super(FrameCypherMessageTooShortError, self).__init__('FrameCypherMessageTooShortError: {}'.format(message))


class FrameCypherMessageInterpretError(FrameCypherException):
    def __init__(self, message=''):
        super(FrameCypherMessageInterpretError, self).__init__('FrameCypherMessageInterpretError: {}'.format(message))


class FrameCypher(object):
    def __init__(self, key='Ilf9DroMDs5kUS0fPo5z2g=='):
        self.key = key

    def encrypt(self, data):
        iv = Random.new().read(AES.block_size)
        return urlsafe_b64encode(iv + AES.new(self.key, AES.MODE_CFB, iv).encrypt(json.dumps(data))).rstrip('=')

    def decrypt(self, message):
        try:
            if (len(message) % 4) != 1:
                # Appending '===' restores omitted '=' and '==' padding
                decoded_message = urlsafe_b64decode(message.encode("utf-8") + '===')
            else:
                # We must reject 4k+1 bytes long strings for they are invalid!
                # (4k+1 bytes long strings are always padded with 'Q' or 'E' and turned into 4k+2 long strings)
                raise FrameCypherMessageInvalidToken('Invalid token length {} ({})'.format(len(message), message))

            # Decoded message must start with AES.block.size bytes of IV value (needed by AES engine)
            if len(decoded_message) > AES.block_size:
                iv = decoded_message[:AES.block_size]
                return json.loads(AES.new(self.key, AES.MODE_CFB, iv).decrypt(decoded_message[AES.block_size:]))
            else:
                raise FrameCypherMessageTooShortError('Invalid token {}'.format(message))
        except TypeError, e:
            raise FrameCypherException('TypeError: {}'.format(e.message))
        except ValueError, e:
            raise FrameCypherException('ValueError: {}'.format(e.message))
