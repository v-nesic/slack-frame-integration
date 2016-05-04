import os

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Greeting
from .slackcmd import execute_slack_slash_command
from .frameinstance import start_frame_instance

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
    return start_frame_instance(request, token)


@csrf_exempt
def slack_slash_cmd_request(request, username):
    return execute_slack_slash_command(request, username)
