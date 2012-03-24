# vim: et:sta:bs=2:sw=4:

import time
import threading

from mirte.core import Module
from sarah.event import Event

class State(Module):
    def __init__(self, *args, **kwargs):
        super(State, self).__init__(*args, **kwargs)
        # events
        self.on_occupation_changed = Event()
        self.on_roomMap_changed = Event()
        self.on_schedule_changed = Event()
        # state
        self.occupation = {}
        self.roomMap = {}
        self._schedule = {}
        # versioning
        self.occupationVersion = 0
        self.roomMapVersion = 0
        self.scheduleVersion = 0
        # internal state
        self.pulling_schedule = False
        self.rooms_considered_for_schedule = None
        self.running = False
        # locks
        self.lock = threading.Lock()
    def run(self):
        self.running = True
        self._pull_schedule_loop()
    def stop(self):
        self.running = False
    def _pull_schedule_loop(self):
        self.pull_schedule()
        if not self.running:
            return
        self.scheduler.plan(time.time() + 60*60*16, self._pull_schedule_loop)
    def pull_schedule(self):
        # We do not want to hold the lock while fetching the new schedule,
        # for that may block for a while.  However, if we do not take the
        # lock, the rooms may have changed in the meantime.  Thus we will
        # simply keep trying until the rooms weren't changed in the mean
        # time.
        while True:
            with self.lock:
                if self.pulling_schedule:
                    self.l.warning("Already pulling schedule")
                    return
                rooms = self.roomMap.keys()
                if not rooms:
                    return
                self.pulling_schedule = True
                roomMapVersion = self.roomMapVersion
            schedule = self.schedule.fetch_todays_schedule(rooms)
            with self.lock:
                self.pulling_schedule = False
                if rooms != self.roomMap.keys():
                    continue # rooms were changed in the meantime
                self.rooms_considered_for_schedule = rooms
                if schedule == self._schedule:
                    break # Nothing changed
                self.l.info("Pulled new schedule; version %s",
                            self.scheduleVersion)
                self._schedule = schedule
                self.scheduleVersion += 1
                self.on_schedule_changed(schedule, self.scheduleVersion)
                break
    def push_occupation_changes(self, occ, source='unknown'):
        roomMap_changed = False
        pull_new_schedule = False
        processed_occ = {}
        with self.lock:
            for pc, state in occ.iteritems():
                pc = pc.lower() # normalize HG075PC47 -> hg075pc47
                # TODO do not hardcode this and put in the client
                if pc.startswith('cz'):
                    continue
                if pc.endswith('docent'):
                    continue
                if pc not in self.occupation or self.occupation[pc] != state:
                    processed_occ[pc] = state
                    self.occupation[pc] = state
                # TODO pull roomMap from ethergids instead of using these
                # heuristics
                roomBit, pcBit = pc.split('pc')
                room = {'hg761': 'HG03.761',
                        'hg206': 'HG00.206',
                        'hg201': 'HG00.201',
                        'hg153': 'HG00.153',
                        'hg137': 'HG00.137',
                        'hg075': 'HG00.075',
                        'hg029': 'HG00.029',
                        'hg023': 'HG00.023',
                        'bib': 'Bibliotheek',
                        'info': 'Infozuilen'}.get(roomBit, roomBit)
                if not room in self.roomMap:
                    self.roomMap[room] = []
                    roomMap_changed = True
                if not pc in self.roomMap[room]:
                    self.roomMap[room].append(pc)
                    roomMap_changed = True
            if roomMap_changed:
                self.roomMapVersion += 1
                roomMap = dict(self.roomMap)
                if (self.rooms_considered_for_schedule != roomMap.keys() and
                        not self.pulling_schedule):
                    pull_new_schedule = True
        if roomMap_changed:
            self.on_roomMap_changed(roomMap, self.roomMapVersion)
        if processed_occ:
            self.occupationVersion += 1
            self.on_occupation_changed(processed_occ, source,
                            self.occupationVersion)
        if pull_new_schedule:
            self.pull_schedule()
    def get_occupation(self):
        with self.lock:
            return (dict(self.occupation), self.occupationVersion)
    def get_roomMap(self):
        with self.lock:
            return (dict(self.roomMap), self.roomMapVersion)
    def get_schedule(self):
        with self.lock:
            return (dict(self._schedule), self.scheduleVersion)
