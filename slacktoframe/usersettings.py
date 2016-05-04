class UserSettings:
    __user_settings = {
        'neske-pilot-project': {
            'token': 'Cb7u0tsogeepryhYkMZwElC5',
            'mapping': {
                'text': 'ljW8ZlGr',
                'image': 'ljW8d7Gr'
            }
        }
    }

    # TODO: check if this is really needed
    def __init__(self):
        pass

    @classmethod
    def add(cls, username, settings):
        if username not in cls.__user_settings:
            cls.__user_settings[username] = settings

    @classmethod
    def override(cls, username, settings):
        if username in cls.__user_settings:
            cls.__user_settings[username] = settings

    @classmethod
    def delete(cls, username):
        if username in cls.__user_settings:
            cls.__user_settings.__delitem__(username)

    @classmethod
    def get(cls, username, value=None, default_value=None):
        if username in cls.__user_settings:
            if value is None:
                return cls.__user_settings[username]
            elif value in cls.__user_settings[username]:
                return cls.__user_settings[username][value]
            else:
                return default_value
        elif value is None:
            return default_value
