# vim: et:sta:bs=2:sw=4:
import re
import datetime
import json
import cStringIO as StringIO

import pycurl

from sarah.cacheDecorators import cacheOnSameArgs
from mirte.core import Module
from tkbd.state import ScheduleError

class MyTimetableError(ScheduleError):
    def __init__(self, inner_exception):
        self.inner_exception = inner_exception
    def __str__(self):
        return "<MyTimetableError `%s'>" % self.inner_exception

_normalize_event_re = [re.compile('(NWI-)?[A-Z0-9]+ ')]
def normalize_event_name(name):
    """ Normalizes the names of reservations.
        eg. "NWI-MOL066 Structure, Function and Bioinformatics"
                --> "Structure, Function and Bioinformatics" """
    return _normalize_event_re[0].sub('', name)

class MyTimetable(Module):
    def open_url(self, url):
        """ Open's URL with apiToken in the headers """
        try:
            c = pycurl.Curl()
            c.setopt(pycurl.FAILONERROR, True)
            c.setopt(pycurl.URL, "%s/api/v0/%s" % (self.url, url))
            c.setopt(pycurl.HTTPHEADER, ["User-Agent: Welke.tk",
                                         "apiToken: %s" % self.apiToken])
            b = StringIO.StringIO()
            c.setopt(pycurl.WRITEFUNCTION, b.write)
            c.setopt(pycurl.FOLLOWLOCATION, 1)
            c.setopt(pycurl.MAXREDIRS, 5)
            
            # Persoonlijkrooster only supports SSLv3, not the default SSLv23.
            c.setopt(pycurl.SSLVERSION, pycurl.SSLVERSION_SSLv3) 
            
            # Verify authenticity of peer's certificate. (0 will not check it)
            c.setopt(pycurl.SSL_VERIFYPEER, 1)
            
            # Verify that domain in URL matches to the Common Name Field or
            # a Subject Alternate Name field in the certificate.
            # (0 will not check it; 1 is an invalid value)
            c.setopt(pycurl.SSL_VERIFYHOST, 2) 
            c.perform()
            return b.getvalue()
        except pycurl.error, e:
            raise MyTimetableError(e)
        assert False

    @cacheOnSameArgs(60*60)
    def fetch_room_ids(self, names):
        """ Fetches the ids of the rooms with the given names """
        ret = {}
        names_set = frozenset(names)
        
        for d in json.loads(self.open_url('timetables?type=location'))['timetable']:
            name = d['hostKey']
            if name in names_set:
                ret[name] = d['value'].encode('utf-8')

        return ret

    @cacheOnSameArgs(60*15)
    def fetch_todays_schedule(self, rooms):
        """ Fetch the schedules for the given rooms. """
        room_ids = self.fetch_room_ids(rooms)

        ret = {}
        now = datetime.datetime.now()
        nowStr = now.strftime('%Y/%m/%d')
        tomorrowStr = (now + datetime.timedelta(days=1)).strftime('%Y/%m/%d')
        
        for room_name in room_ids:
            ret[room_name] = []

            events = json.loads(self.open_url("timetables/%s?startDate=%s&endDate=%s" % (room_ids[room_name], nowStr, tomorrowStr)))

            for event in events:
                starttime = datetime.datetime.fromtimestamp(event['startDate']/1000.0)
                endtime = datetime.datetime.fromtimestamp(event['endDate']/1000.0)

                description = event['activityDescription']
                if description is None:
                    description = event['notes']
                
                if description is None:
                    description = '( geen omschrijving )'
                
                ret[room_name].append((starttime, endtime, normalize_event_name(description)))

        return ret

if __name__ == '__main__':
    r = MyTimetable({'url': 'https://persoonlijkrooster-acc.ru.nl', 'apiToken': 'sekreet'}, None)
    import pprint
    pprint.pprint(r.fetch_todays_schedule(['HG00.075', 'HG00.201', 'HG00.206',
                'HG00.153', 'HG00.137', 'HG00.023', 'HG03.761', 'HG00.029']))
