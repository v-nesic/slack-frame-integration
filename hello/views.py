import os
import requests

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Greeting

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

@csrf_exempt
def slack(request):
	if request.POST.get('token', '') == 'Cb7u0tsogeepryhYkMZwElC5':
		return HttpResponse('{"text":"http://fra.me"}', content_type='application/json')
	else:
		return HttpResponse('You can set up your FRAME account at http://fra.me')