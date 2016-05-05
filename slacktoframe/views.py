import json

from django.shortcuts import render
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from .slackcmd import SlackCmdFrame
from .crypto import FrameCypher, FrameCypherException


@csrf_exempt
def slack_slash_cmd_request(request, username):
    if request.POST.get('command', '') == '/frame':
        return SlackCmdFrame.execute(request, username)
    else:
        return HttpResponseBadRequest('400 BAD REQUEST: Command {} unknown'.format(request.POST.get('command', '')))


def frame_instance_request(request, token):
    try:
        return render(request, 'frame-instance.html', FrameCypher().decrypt(token))
    except FrameCypherException, e:
        return HttpResponseBadRequest('400 NOT FOUND {}, error = {}'.format(request.path, e.message))
