import json
import re
import urllib2

from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.core.urlresolvers import reverse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from .crypto import FrameCypher
from .usersettings import UserSettings


###############################################################################################
# SlackCmd exceptions
class SlackCmdException(BaseException):
    def __init__(self, error=''):
        self.error = error

    def get_error(self):
        return self.error


class SlackCmdRequestException(SlackCmdException):
    def __init__(self, error):
        SlackCmdException.__init__(self, "SlackCmdRequestException: {}".format(error))


class SlackCmdFrameAuthenticationException(SlackCmdException):
    def __init__(self, error=''):
        SlackCmdException.__init__(self, "SlackCmdFrameAuthenticationException: {}".format(error))


class SlackCmdFrameFileError(SlackCmdException):
    def __init__(self, error):
        SlackCmdException.__init__(self, 'SlackCmdFrameFileError: {}'.format(error))


class SlackCmdFrameUnsupportedFileTypeError(SlackCmdException):
    def __init__(self, error):
        SlackCmdException.__init__(self, 'SlackCmdFrameUnsupportedFileTypeError: {}'.format(error))


###############################################################################################
# Generic Slack command class
class SlackCmd:
    def __init__(self, request):
        supported_arguments = [
            'token', 'team_id', 'team_domain', 'channel_id', 'channel_name',
            'user_id', 'user_name', 'command', 'text', 'response_url'
        ]
        self.request = request
        self.arguments = {}
        for arg in supported_arguments:
            self.arguments[arg] = request.POST.get(arg, None)

        for arg in supported_arguments:
            if self.arguments[arg] is not None:
                SlackCmd.validate_argument(arg, self.arguments[arg])
            else:
                raise SlackCmdRequestException('Missing mandatory POST arg {}'.format(arg))

    @staticmethod
    def validate_argument(arg, arg_value):
        if arg != 'text' and arg_value == '':
            raise SlackCmdRequestException('POST arg {} contains invalid value {}'.format(arg, arg_value))

    def get_command(self):
        return self.arguments['command']

    def get_arguments(self):
        return self.arguments


###############################################################################################
# Helper class for getting HTTP header rather than complete file
class HttpRequestHead(urllib2.Request):
    def get_method(self):
        return "HEAD"


###############################################################################################
# /frame command class
class SlackCmdFrame(SlackCmd):
    help_response_text = 'Usage: /frame FILE_URL'
    url_response_attachment_text = 'Click at the returned URL in order to open your file in FRAME instance'

    def __init__(self, request, username):
        SlackCmd.__init__(self, request)
        if username is not None and self.authenticate(username):
            self.username = username
        else:
            self.username = None
            raise SlackCmdFrameAuthenticationException(
                'Wrong username,token pair ({},{})'.format(username, self.arguments['token'])
            )

    def authenticate(self, username):
        assert username is not None
        assert 'token' in self.arguments
        assert self.arguments['token'] is not None

        return self.arguments['token'] == UserSettings.get(username, 'token')

    @staticmethod
    def get_http_json_response(text, attachment_text=None):
        response = {'text': text}
        if attachment_text is not None:
            response['attachments'] = {'text': attachment_text}
        return JsonResponse(response)

    @staticmethod
    def get_help_response():
        return SlackCmdFrame.get_http_json_response(SlackCmdFrame.help_response_text)

    @staticmethod
    def validate_url(file_url):
        try:
            # If the URL doesn't begin with scheme, we shall default to http://
            if re.search('^[a-zA-Z]+://', file_url) is None:
                file_url = 'http://' + file_url
            URLValidator()(file_url)
            return file_url
        except ValidationError:
            raise SlackCmdFrameFileError("Requested file URL {} is invalid".format(file_url))

    @staticmethod
    def get_content_type(file_url):
        # We deduct file type from using it's content-type header rather than extension.
        # As a side benefit, we also confirm that the file is accessible before allowing
        # it to start a Frame instance.
        try:
            response = urllib2.urlopen(HttpRequestHead(file_url))
        except urllib2.HTTPError, e:
            raise SlackCmdFrameFileError('HTTP ERROR {} received while trying to open requested file'.format(e.code))
        except:  # Catch-all exception should be OK here because we don't really care why the file can't be accessed
            raise SlackCmdFrameFileError('Unknown ERROR while trying to open requested file')

        # TODO: Decide if we should make additional checks for servers which don't support HEAD
        if response.getcode() != 200:
            raise SlackCmdFrameFileError(
                'HTTP ERROR {} received while accessing file {} headers'.format(response.getcode(), file_url)
            )

        # We need only the beginning of content-type (i.e. text from text/plain or image from image/png)
        content_type = response.info().getheader('content-type')
        slash_pos = content_type.find('/')
        if slash_pos > 0:  # discard content-types with no slash or with a slash as the fist char
            return content_type[:slash_pos]
        else:
            raise SlackCmdFrameFileError('Unknown content type {}'.format(content_type))

    @staticmethod
    def get_file_type(file_url):
        return SlackCmdFrame.get_content_type(file_url)

    def get_application_id(self, file_type):
        application_id = UserSettings.get(self.username, 'application_id')
        if file_type in application_id:
            return application_id[file_type]
        else:
            raise SlackCmdFrameUnsupportedFileTypeError(file_type)

    def get_file_response(self):
        file_url = SlackCmdFrame.validate_url(self.arguments['text'])
        token = FrameCypher().encrypt({
            'file_url': file_url,
            'application_id': self.get_application_id(self.get_file_type(file_url)),
            'pool_id': UserSettings.get(self.username, 'pool_id')
        })
        frame_instance_url = 'https://' + self.request.get_host() + reverse('frame-instance', args=[token])

        return self.get_http_json_response(frame_instance_url, self.url_response_attachment_text)

    @staticmethod
    def execute(request, username):
        try:
            command = SlackCmdFrame(request, username)
            if command.arguments['text'] == '' or command.arguments['text'].lower() == 'help':
                return command.get_help_response()
            else:
                return command.get_file_response()
        except (SlackCmdRequestException, SlackCmdFrameFileError, SlackCmdFrameUnsupportedFileTypeError), e:
            return HttpResponseBadRequest('400 BAD REQUEST {}'.format(e.get_error()))
        except SlackCmdFrameAuthenticationException, e:
            return HttpResponseForbidden('403 FORBIDDEN {}'.format(e.get_error()))
