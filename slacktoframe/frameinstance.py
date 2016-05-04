from django.shortcuts import render
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound

from .crypto import FrameCypher


def start_frame_instance(request, token):
    return HttpResponseBadRequest('Not implemented')

def tobereused(request, token):
    try:
        mapping_and_file = FrameCypher().decrypt(token)
        split = mapping_and_file.find(':')
        if split == -1:
            return HttpResponseNotFound(
                '400 NOT FOUND {}, split = {}, mapping_and_file={}'.format(request.path, split, mapping_and_file))

        context = {
            'mapping': mapping_and_file[:split],
            'file_url': mapping_and_file[split:]
        }
        return render(request, 'frame-instance.html', context)
    except BaseException, e:
        return HttpResponseNotFound('400 NOT FOUND {}, error = {}'.format(request.path, e))
