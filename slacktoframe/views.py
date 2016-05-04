import os

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from .models import Greeting
from .slackcmd import SlackCmdFrame
from .crypto import FrameCypher, FrameCypherException

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


def frame_instance_request(request, token):
    try:
        file_mapping, file_url = FrameCypher().decrypt(token)
        return render(request, 'frame-instance.html', {'mapping': file_mapping, 'file_url': file_url})
    except FrameCypherException, e:
        return HttpResponseBadRequest('400 NOT FOUND {}, error = {}'.format(request.path, e.get_error()))


@csrf_exempt
def slack_slash_cmd_request(request, username):
    if request.POST.get('command', '') == '/frame':
        return SlackCmdFrame.execute(request, username)
    else:
        return HttpResponseBadRequest('400 BAD REQUEST: Command {} unknown'.format(request.POST.get('command', '')))
