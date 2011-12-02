# vim: et:sta:bs=2:sw=4:
import urllib2
import datetime

import msgpack

from sarah.cacheDecorators import cacheOnSameArgs

from mirte.core import Module

DAYS = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su']

class Ruuster(Module):
    @cacheOnSameArgs(60*60*24)
    def fetch_inst_id(self):
        """ Fetches the institute id of the RU """
        for d in msgpack.unpack(urllib2.urlopen(
                "%s/list/institutes?format=msgpack" % self.url)):
            if d['name'] == 'Radboud Universiteit Nijmegen':
                return d['id']
        assert False

    @cacheOnSameArgs(60*60)
    def fetch_room_ids(self, names):
        """ Fetches the ids of the rooms with the given names """
        ret = {}
        names_set = set(names)
        for d in msgpack.unpack(urllib2.urlopen(
                "%s/list/locations?format=msgpack" % self.url)):
            name = d['name'].upper() # normalize: Hg -> HG
            if name in names_set:
                ret[name] = d['id']
        return ret

    @cacheOnSameArgs(60*15)
    def fetch_todays_schedule(self, rooms):
        """ Fetch the schedules for the given rooms. """
        room_ids = self.fetch_room_ids(rooms)
        inst_id = self.fetch_inst_id()
        ret = {}
        now = datetime.datetime.now()
        day = DAYS[now.isoweekday() - 1]
        for room_name in room_ids:
            ret[room_name] = []
            events = msgpack.unpack(urllib2.urlopen(
                "%s/snapshot/head/%s/location/%s?format=msgpack" % (
                    self.url, inst_id, room_ids[room_name])))['events']
            for event in events:
                starttime = datetime.datetime.strptime(
                        event['starttime'], '%H:%M:%S').time()
                endtime = datetime.datetime.strptime(
                        event['endtime'], '%H:%M:%S').time()
                if event['day'] != day:
                    continue
                ok = False
                for period in event['eventperiods']:
                    startdate = datetime.datetime.strptime(
                            period['startdate'], '%Y-%m-%d %H:%M:%SZ').date()
                    enddate = datetime.datetime.strptime(
                            period['enddate'], '%Y-%m-%d %H:%M:%SZ').date()
                    if (startdate <= now.date() and now.date() <= enddate):
                        ok = True
                        break
                if not ok:
                    continue
                ret[room_name].append((starttime, endtime,
                        event['course']['name']))
        return ret

if __name__ == '__main__':
    r = Ruuster({'url': 'http://api.ruuster.nl'}, None)
    import pprint
    pprint.pprint(r.fetch_todays_schedule(['HG00.075', 'HG00.201', 'HG02.206',
                'HG00.153', 'HG00.137', 'HG00.023', 'HG03.761', 'HG00.029']))
