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
from .slackcmd import SlackCmdFrame
from .slackcmd import SlackCmdRequestException
from .slackcmd import SlackCmdFrameFileError
from .slackcmd import SlackCmdFrameUnsupportedFileTypeError
from .slackcmd import SlackCmdFrameAuthenticationException

# Create your views here.
def index(request):
    times = int(os.environ.get('TIMES',3))
    response = request.GET.get('q', 'Hello! ' * times)
    return HttpResponse(response)
    #r = requests.get('http://httpbin.org/status/418')
    #print r.text
    #return HttpResponse('<pre>' + r.text + '</pre>')
    # return HttpResponse('Hello from Python!')
    # return render(request, 'index.html')


def db(request):

    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, 'db.html', {'greetings': greetings})


def frame(request, token):
    try:
        mapping_and_file = FrameCypher().decrypt(token)
        split = mapping_and_file.find(':')
        if split == -1:
            return HttpResponseNotFound('400 NOT FOUND {0}, split = {1}, mapping_and_file={2}'.format(request.path, split, mapping_and_file))

        context = {
            'mapping': mapping_and_file[:split],
            'file_url': mapping_and_file[split:]
        }
        return HttpResponse(json.dumps(context), content_type='application/json')
        # return render(request, 'frame-instance-run.html', context)
    except BaseException, e:
        return HttpResponseNotFound('400 NOT FOUND {0}, error = {1}'.format(request.path, e))


@csrf_exempt
def slackSlashCmdRequest(request, username):
    try:
        command = request.POST.get('command', '')
        if command == '/frame':
            return SlackCmdFrame(request, username).handle()
        else:
            return HttpResponseBadRequest('400 BAD REQUEST: Command {0} unknown'.format(command))
    except (SlackCmdRequestException, SlackCmdFrameFileError, SlackCmdFrameUnsupportedFileTypeError), e:
        return HttpResponseBadRequest('400 BAD REQUEST {0}'.format(e.get_error()))
    except SlackCmdFrameAuthenticationException, e:
        return HttpResponseForbidden('403 FORBIDDEN {0}'.format(e.get_error()))
