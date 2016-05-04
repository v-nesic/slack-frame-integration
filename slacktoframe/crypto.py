from base64 import urlsafe_b64encode
from base64 import urlsafe_b64decode
from Crypto.Cipher import AES
from Crypto import Random


class FrameCypherException(BaseException):
    def __init__(self, error=''):
        self.error = error

    def get_error(self):
        return self.error


class FrameCypherMessageInvalidToken(FrameCypherException):
    def __init__(self, error=''):
        FrameCypherException.__init__(self, 'FrameCypherMessageInvalidToken: {}'.format(error))


class FrameCypherMessageTooShortError(FrameCypherException):
    def __init__(self, error=''):
        FrameCypherException.__init__(self, 'FrameCypherMessageTooShortError: {}'.format(error))


class FrameCypherMessageInterpretError(FrameCypherException):
    def __init__(self, error=''):
        FrameCypherException.__init__(self, 'FrameCypherMessageInterpretError: {}'.format(error))


class FrameCypher:
    def __init__(self, key='Ilf9DroMDs5kUS0fPo5z2g=='):
        self.key = key

    @staticmethod
    def combine(file_type_mapping, file_url):
        return '{}:{}'.format(file_type_mapping, file_url)

    @staticmethod
    def split(message):
        split = message.find(':')
        if split > 0:
            return message[:split], message[split+1:]
        else:
            raise FrameCypherMessageInterpretError(message)

    def encrypt(self, file_type_mapping, file_url):
        iv = Random.new().read(AES.block_size)

        # Combine file mapping and url into single string and return base64 encoded token without '=' padding
        return urlsafe_b64encode(
            iv + AES.new(self.key, AES.MODE_CFB, iv).encrypt(FrameCypher.combine(file_type_mapping, file_url))
        ).rstrip('=')

    def decrypt(self, message):
        try:
            if (len(message) % 4) == 1:
                # We must reject 4k+1 bytes long strings for they are invalid!
                # (4k+1 bytes long strings are always padded with 'Q' or 'E' and turned into 4k+2 long strings)
                raise FrameCypherMessageInvalidToken('Invalid token length {} ({})'.format(len(message), message))

            # Appending '===' restores omitted '=' and '==' padding
            decoded_message = urlsafe_b64decode(message.encode("utf-8") + '===')

            # Decoded message must start with AES.block.size bytes of IV value (needed by AES engine)
            if len(decoded_message) > AES.block_size:
                iv = decoded_message[:AES.block_size]
            else:
                raise FrameCypherMessageTooShortError('Invalid token {}'.format(message))

            # Decode, split into (mapping, url) pair and return
            return FrameCypher.split(AES.new(self.key, AES.MODE_CFB, iv).decrypt(decoded_message[AES.block_size:]))
        except TypeError, e:
            raise FrameCypherException('TypeError: {}'.format(e.message))
        except ValueError, e:
            raise FrameCypherException('ValueError(iv = {}):{}'.format(iv, e.message))
