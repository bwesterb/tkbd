import urllib2
import datetime

import msgpack

BURL = 'http://api.ruuster.nl'
DAYS = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su']

def fetch_schedule(room_ids, inst_id):
        """ Fetch (and filter) the schedule for the given rooms.  Wil return
            for each room the current or first event. """
        ret = {}
        now = datetime.datetime.now()
        day = DAYS[now.isoweekday() + 1]
        for room_name in room_ids:
                nigh_event = None
                events = msgpack.unpack(urllib2.urlopen(
                        "%s/snapshot/head/%s/location/%s?format=msgpack" % (
                                BURL, inst_id, room_ids[room_name])))['events']
                for event in events:
                        starttime = datetime.datetime.strptime(
                                        event['starttime'], '%H:%M:%S').time()
                        endtime = datetime.datetime.strptime(event['endtime'],
                                        '%H:%M:%S').time()
                        if endtime < now.time():
                                continue
                        if event['day'] != day:
                                continue
                        ok = False
                        for period in event['eventperiods']:
                                startdate = datetime.datetime.strptime(
                                                period['startdate'],
                                                '%Y-%m-%d %H:%M:%SZ')
                                enddate = datetime.datetime.strptime(
                                                period['enddate'],
                                                '%Y-%m-%d %H:%M:%SZ')
                                if startdate <= now and now <= enddate:
                                        ok = True
                                        break
                        if not ok:
                                continue
                        if nigh_event is None or starttime <= nigh_event[0]:
                                nigh_event = (starttime, endtime,
                                                event['course']['name'])
                ret[room_name] = nigh_event
        return ret

def fetch_inst_id():
        """ Fetches the institute id of the RU """
        for d in msgpack.unpack(urllib2.urlopen(
                        "%s/list/institutes?format=msgpack" % BURL)):
                if d['name'] == 'Radboud Universiteit Nijmegen':
                        return d['id']
        assert False

def fetch_room_ids(names):
        """ Fetches the ids of the rooms with given names """
        ret = {}
        names_set = set(names)
        for d in msgpack.unpack(urllib2.urlopen(
                        "%s/list/locations?format=msgpack" % BURL)):
                name = d['name'].upper() # normalize: Hg -> HG
                if name in names_set:
                        ret[name] = d['id']
        return ret

if __name__ == '__main__':
        inst_id = fetch_inst_id()
        print inst_id
        room_ids = fetch_room_ids(
                ['HG00.201', 'HG00.206', 'HG03.761', 'HG02.702', 'HG00.075',
                 'HG00.029', 'HG00.002', 'HG00.153', 'HG00.137', 'HG00.023',
                 'HG00.401', 'HG00.149'])
        print room_ids
        print fetch_schedule(room_ids, inst_id)
