import os
import tempfile

from django.http import HttpResponse, HttpResponseNotAllowed
from django.utils import simplejson as json
import flickr

def json_response(**obj):
    return HttpResponse(json.dumps(obj), mimetype='application/json')

def upload_to_flickr(req, upload=flickr.upload):
    fd, tempfilename = tempfile.mkstemp(suffix='.png')
    os.close(fd)
    f = open(tempfilename, 'wb')
    for chunk in req.FILES['screenshot'].chunks():
        f.write(chunk)
    f.close()
    
    try:
        photo_id = upload(
            filename=tempfilename,
            title=req.POST.get('title', 'Untitled'),
            description=req.POST.get('description', ''),
            content_type=2
            )
    finally:
        os.remove(tempfilename)

    return photo_id

# Create your views here.
def upload(req, upload_to_flickr=upload_to_flickr):
    if req.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    photo_id = upload_to_flickr(req)

    return json_response(
        photo_id=photo_id
        )
