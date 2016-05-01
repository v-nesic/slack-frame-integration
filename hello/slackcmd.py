import json
import os
import requests
import urllib2

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.conf.urls import url
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from functools import wraps

from .crypto import FrameCypher
from .models import Greeting


###############################################################################
# Base class for handling Slack command exceptions
class SlackCmdException(BaseException):
    def __init__(self, error=''):
        self.error = error

    def get_error(self):
        return self.error


###############################################################################
# Generic Slack command validation
###############################################################################
# Global variable (shared between this code and test) listing required slack cmd arguments
slack_cmd_post_args = [
    'token', 'team_id', 'team_domain', 'channel_id', 'channel_name',
    'user_id', 'user_name', 'command', 'text', 'response_url'
]


class SlackCmdRequestException(SlackCmdException):
    def __init__(self, error):
        SlackCmdException.__init__(self, "SlackCmdRequestException: {0}".format(error))


def validate_slack_cmd_argument(arg, arg_value):
    if arg != 'text' and arg_value == '':
        raise SlackCmdRequestException('POST arg {0} contains invalid value {1}'.format(arg, arg_value))


def validate_slack_cmd_requst(request):
    slack_cmd_args = {}
    for arg in slack_cmd_post_args:
        slack_cmd_args[arg] = request.POST.get(arg, None)

    for arg in slack_cmd_post_args:
        if slack_cmd_args[arg] is None:
            raise SlackCmdRequestException('Missing mandatory POST arg {0}'.format(arg))
        else:
            validate_slack_cmd_argument(arg, slack_cmd_args[arg])

    return slack_cmd_args


###############################################################################
# Slack team vs. token authentication
###############################################################################
# Exception class for handling authentication errors such as invalid (groupId, token) pair
class SlackCmdFrameAuthenticationException(SlackCmdException):
    def __init__(self, error=''):
        SlackCmdException.__init__(self, "SlackCmdFrameAuthenticationException: {0}".format(error))


def authenticate_slack_cmd_frame_args(slack_cmd_args):
    if slack_cmd_args['team_id'] != 'T10V1PSR4':
        raise SlackCmdFrameAuthenticationException('FRAME team_id = {0}'.format(slack_cmd_args['team_id']))
    if slack_cmd_args['token'] != 'Cb7u0tsogeepryhYkMZwElC5':
        raise SlackCmdFrameAuthenticationException('FRAME token = {0}'.format(slack_cmd_args['token']))


class SlackCmdFrameFileError(BaseException):
    error = ''

    def __init__(self, error):
        self.error = error

    def get_error(self):
        return self.error

class HeaderRequest(urllib2.Request):
    def get_method(self):
        return "HEAD"


def validate_url_format(url):
    validate = URLValidator()
    validate(url)


def file_type(file):
    try:
        validate_url_format(file)
        response = urllib2.urlopen(HeaderRequest(file))
        if response.getcode() == 200:
            return response.info().getheader('content-type')
        else:
            raise SlackCmdFrameFileError('ERROR {0} received while trying to open requested file'.format(response.getcode()))
    except ValidationError, e:
        raise SlackCmdFrameFileError("Requested file URL is invalid")
    except urllib2.HTTPError, e:
        raise SlackCmdFrameFileError('HTTP ERROR {0} received while trying to open requested file'.format(e.code))
    except:
        # Catch-all exception is OK here because it means that
        # we can't access requested file and we don't really
        # care why
        raise SlackCmdFrameFileError('Unknown ERROR while trying to open requested file')


def slack_cmd_error_invalid_file_type_message(type):
    return SlackCmdFrameFileError("File type {0} is not supported".format(type))


def get_file_mapping_and_type(file):
    # Check file type
    type = file_type(file)
    if 'text/' == type[:5]:
        return 'ljW8ZlGr', 'TEXT'
    elif 'image/' == type[:6]:
        raise slack_cmd_error_invalid_file_type_message('IMAGE') # TODO: add mapping for this one too
    else:
        raise slack_cmd_error_invalid_file_type_message(type)


def slack_frame_response(request, mapping, file, file_type):
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

def handle_slack_cmd_frame(slack_cmd_args):
    authenticate_slack_cmd_frame_args(slack_cmd_args)
    if slack_cmd_args['text'] == 'help':
        return HttpResponse("Help text")
    else:
        return HttpResponse(json.dumps(slack_cmd_args))


def handle_request(request, command):
    try:
        slack_cmd_args = validate_slack_cmd_requst(request)

        if slack_cmd_args['command'] != command:
            raise SlackCmdRequestException("Posted command arg {0} doesn't match url command arg {1}".format(slack_cmd_args['command'], command))

        if '/frame' == command:
            return HttpResponse(json.dumps(request.POST))
            # return handle_slack_cmd_frame(slack_cmd_args)
        else:
            raise SlackCmdRequestException('Unknown command {0}'.format(command))

    except SlackCmdRequestException, e:
        return HttpResponseBadRequest('400 BAD REQUEST {0}'.format(e.get_error()))

    except SlackCmdFrameAuthenticationException, e:
        return HttpResponseForbidden('403 FORBIDDEN {0}'.format(e.get_error()))

        # Get requested file URL
        #file = request.POST.get('text', 'https://www.google.rs/images/nav_logo242.png')
        #file = request.POST.get('text', 'https://www.google.com')
        #file = request.POST.get('text', 'https://www.google.com/xpy')
        #file = request.POST.get('text', 'xpy')

        # Get file mapping
        #mapping, file_type = get_file_mapping_and_type(file)

        #return HttpResponse(json.dumps(slack_frame_response(request, mapping, file, file_type)), content_type='application/json')

    #except SlackCmdFrameFileError:
        #return HttpResponseBadRequest('400 BAD REQUEST')


    #return HttpResponse(json.dumps(response), content_type='application/json')
    #return HttpResponse(("https://" if request.is_secure() else "http://") + request.get_host() + reverse('slack-cmd-frame'))
    #if request.POST.get('token', '') == 'Cb7u0tsogeepryhYkMZwElC5':
    #    return HttpResponse('{"text":"http://fra.me"}', content_type='application/json')
    #else:
    #    return HttpResponse('You can set up your FRAME account at http://fra.me')


