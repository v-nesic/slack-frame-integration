import json
import os
import requests
import urllib2

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.conf.urls import url
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from functools import wraps

from .crypto import FrameCypher
from .models import Greeting


###############################################################################################
# SlackCmd exceptions
class SlackCmdException(BaseException):
    def __init__(self, error=''):
        self.error = error

    def get_error(self):
        return self.error


class SlackCmdRequestException(SlackCmdException):
    def __init__(self, error):
        SlackCmdException.__init__(self, "SlackCmdRequestException: {0}".format(error))


class SlackCmdFrameAuthenticationException(SlackCmdException):
    def __init__(self, error=''):
        SlackCmdException.__init__(self, "SlackCmdFrameAuthenticationException: {0}".format(error))


class SlackCmdFrameFileError(SlackCmdException):
    def __init__(self, error):
        SlackCmdException.__init__(self, 'SlackCmdFrameFileError: {0}'.format(error))


class SlackCmdFrameUnsupportedFileTypeError(SlackCmdException):
    def __init__(self, error):
        SlackCmdException.__init__(self, 'SlackCmdFrameUnsupportedFileTypeError: {0}'.format(error))


###############################################################################################
# Helper class for getting HTTP header rather than complete file
class HeaderRequest(urllib2.Request):
    def get_method(self):
        return "HEAD"


###############################################################################################
# Generic Slack command class
class SlackCmd:
    def __init__(self, request):
        supported_arguments = [
            'token', 'team_id', 'team_domain', 'channel_id', 'channel_name',
            'user_id', 'user_name', 'command', 'text', 'response_url'
        ]
        self.arguments = {}
        for arg in supported_arguments:
            self.arguments[arg] = request.POST.get(arg, None)

        for arg in supported_arguments:
            if self.arguments[arg] is not None:
                self.validateArgument(arg, self.arguments[arg])
            else:
                raise SlackCmdRequestException('Missing mandatory POST arg {0}'.format(arg))

    @staticmethod
    def validateArgument(arg, arg_value):
        if arg != 'text' and arg_value == '':
            raise SlackCmdRequestException('POST arg {0} contains invalid value {1}'.format(arg, arg_value))

    def getCommand(self):
        return self.arguments['command']

    def getArguments(self):
        return self.arguments


###############################################################################################
# /frame command class
class SlackCmdFrame(SlackCmd):
    def __init__(self, request, username):
        SlackCmd.__init__(self, request)
        self.authenticate(username, self.getArguments()['token'])

    @staticmethod
    def authenticate(username, token):
        if username == 'neske-pilot-project' and token == 'Cb7u0tsogeepryhYkMZwElC5':
            pass
        elif username == 'test.username' and token == 'test.token':
            pass
        else:
            raise SlackCmdFrameAuthenticationException('Wrong username,token pair ({0},{1})'.format(username, token))

    def validateUrl(self, url):
        validate = URLValidator()
        validate(url)

    def getFileType(self, file):
        try:
            self.validateUrl(file)
            response = urllib2.urlopen(HeaderRequest(file))
            if response.getcode() != 200:
                raise SlackCmdFrameFileError('ERROR {0} received while trying to open requested file'.format(response.getcode()))
            return response.info().getheader('content-type')
        except ValidationError, e:
            raise SlackCmdFrameFileError("Requested file URL is invalid")
        except urllib2.HTTPError, e:
            raise SlackCmdFrameFileError('HTTP ERROR {0} received while trying to open requested file'.format(e.code))
        except:
            # Catch-all exception is OK here because it means that we can't access requested file
            # and we don't really care why
            raise SlackCmdFrameFileError('Unknown ERROR while trying to open requested file')

    def getFileMappingAndType(self, file):
        # Check file type
        type = self.getFileType(file)
        if 'text/' == type[:5]:
            return 'ljW8ZlGr', 'TEXT'
        elif 'image/' == type[:6]:
            raise SlackCmdFrameUnsupportedFileTypeError('IMAGE') # TODO: add mapping for this one too
        else:
            raise SlackCmdFrameUnsupportedFileTypeError(type)

    def handleFile(self, request, mapping, file, file_type):
        # Calculate URL parts...
        schema = 'https://' if request.is_secure() else 'http://'
        host = request.get_host()
        path = reverse('frame-instance-run', args=[FrameCypher().encrypt(':'.join([mapping, file]))])

        # ...merge them into URL...
        url = ''.join([schema, host, path])

        # ...and combine everything into a signle JSON response
        return {
            'text': url,
            'attachments': {
                'text': 'Click at the returned URL in order to open your file in FRAME instance',
                'url': url,
                'file_type': file_type
            }
        }

    def handle(self):
        if self.arguments['text'].lower() == 'help':
            return HttpResponse("Help text")
        else:
            return HttpResponse(json.dumps(self.arguments))
