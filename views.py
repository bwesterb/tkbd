# vim: et:sta:bs=2:sw=4:
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.core.servers.basehttp import FileWrapper
from django.core.exceptions import PermissionDenied
from django.shortcuts import render_to_response
from django.http import HttpResponse, Http404
from django.template import RequestContext
from django.core.cache import cache

from tkb.http import JsonishHttpResponse
from tkb.ruuster import fetch_schedule, fetch_inst_id, fetch_room_ids
from tkb.state import set_occupation_of_multiple, get_occupation

import mimetypes
import datetime
import logging
import os.path
import urllib2
import json
import os

def direct_to_folder(request, root, path):
    """ Serves files under <root> statically.

    Used to serve /media. """
    root = os.path.abspath(root)
    p = os.path.abspath(os.path.join(root, path))
    if not p.startswith(root):
        raise PermissionDenied, "Going outside of the root"
    if not os.path.exists(p):
        raise Http404
    if not os.path.isfile(p):
        raise PermissionDenied, "This is not a file"
    if os.stat(p).st_mode & 4 != 4:
        raise PermissionDenied, "Not world readable"
    return HttpResponse(FileWrapper(open(p)),
            mimetype=mimetypes.guess_type(p)[0])

def home(request):
    """ Main view """
    return render_to_response('home.html',
            context_instance=RequestContext(request))

def _api():
    ret = {'format': 1,
           'generated': str(datetime.datetime.now())}
    # generate occupation by room
    occup = {}
    for pc, state in get_occupation().items():
        room = pc.split('pc')[0]
        if not room in occup:
            occup[room] = [0, 0]
        if state['status'] == 'free':
            occup[room][0] += 1
        else:
            occup[room][1] += 1
    # fetch schedule from api.ruuster.nl
    schedule = cache.get('schedule')
    if schedule is None: # cache miss
        try:
            room_ids = cache.get('ruuster-roomids')
            if room_ids is None: # cache miss
                room_ids = fetch_room_ids(occup.keys())
                cache.set('ruuster-roomids', room_ids, 60*60)
            inst_id = cache.get('ruuster-instid')
            if inst_id is None: # cache miss
                inst_id = fetch_inst_id()
                cache.set('ruuster-instid', inst_id, 60*60)
            schedule = fetch_schedule(room_ids, inst_id)
            cache.set('schedule', schedule, 60)
        except urllib2.HTTPError:
            # We do not want our service to be down, when
            # ruuster is down.
            # TODO be agnostic of ruuster.py's usage of urllib2
            l.exception("HTTPError from ruuster")
            schedule = {}
    # combine
    rooms = ret['rooms'] = []
    for room_name in occup:
        res = schedule.get(room_name)
        if res is not None:
            res = {'starttime': res[0].strftime('%H:%M'),
                   'endtime': res[1].strftime('%H:%M'),
                   'now': res[0] <= datetime.datetime.now().time(),
                   'name': res[2]}
        rooms.append({
            'name': room_name,
            'free': occup[room_name][0],
            'capacity': occup[room_name][0] + occup[room_name][1],
            'reservation': res})
    # sort rooms by name
    rooms.sort(cmp=lambda x,y: cmp(x['name'], y['name']))
    return ret

def api(request):
    """ Returns the occupation """
    l = logging.getLogger(__name__ + '.api')
    ret = cache.get('views-api')
    if ret is None:
        ret = _api()
        cache.set('views-api', ret, 1)
    return JsonishHttpResponse(ret,
            format=request.REQUEST.get('format', 'json'))

@csrf_exempt
def push(request):
    """ Called by our datasource to push changes to occupation """
    l = logging.getLogger(__name__ + '.push')
    # TODO authenticate client
    d = json.loads(request.raw_post_data)
    l.debug("received: %s" % repr(d))
    # We expect
    #  { 'datasoure': 'scan' | 'log',
    #    'data': { <pc>: {'status': 'free' | 'used' | 'unknown',
    #                     'session': 'windows' | 'linux' } } }
    source = d.get('datasource', 'unknown')
    occ_updates = {}
    for pc, state in d['data'].items():
        occ_updates[pc] = {'status': state.get('status'),
                           'session': state.get('session')}
    set_occupation_of_multiple(occ_updates)
    return JsonishHttpResponse(True)
