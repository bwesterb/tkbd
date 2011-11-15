# vim: et:sta:bs=2:sw=4:

import json
import msgpack

from django.http import HttpResponse

JSONISH_FORMATS = ['json', 'prettyJson', 'msgpack']

class JsonishHttpResponse(HttpResponse):
    def __init__(self, obj, *args, **kwargs):
        fmt = 'json'
        if 'format' in kwargs:
            if kwargs['format'] in JSONISH_FORMATS:
                fmt = kwargs['format']
            del kwargs['format']
        if fmt == 'json':
            mimetype = 'application/json'
            txt = json.dumps(obj)
        elif fmt == 'prettyJson':
            mimetype = 'application/json'
            txt = json.dumps(obj, indent=2)
        elif fmt == 'msgpack':
            mimetype = 'application/x-msgpack'
            txt = msgpack.packb(obj)
        kwargs['mimetype'] = mimetype
        super(JsonishHttpResponse, self).__init__(txt, *args, **kwargs)
