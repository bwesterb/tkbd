# vim: et:sta:bs=2:sw=4:

import time
import threading
import collections

from copy import deepcopy, copy

from mirte.core import Module
from sarah.event import Event

roomMap_entry = collections.namedtuple('roomMap_entry', ('name', 'pcs'))

class ScheduleError(Exception):
    pass

class State(Module):
    def __init__(self, *args, **kwargs):
        super(State, self).__init__(*args, **kwargs)
        # simple events
        self.on_tagMap_changed = Event()
        # listeners for events by filters.
        #  Each of them is a dictionary
        #    { <filter>: <callbacks> }
        #  where <filter> is a tuple of tags and <callbacks> are the functions
        #  that want to be notified when events happen related to these tags.
        self.occupation_listeners = {}
        self.roomMap_listeners = {}
        self.schedule_listeners = {}
        # STATE
        #  { <pc-name>: <occupation> }
        self.occupation = {}
        #  { <room-id>: [<name>, [<pc-name>, ...]] }
        #  The roomMap is partially hardcoded and updated on the fly by
        #  guesses.  TODO We should allow the sources to push roomMaps.
        self.roomMap = {'hg761':  roomMap_entry('HG03.761', set()),
                        'hg206':  roomMap_entry('HG00.206', set()),
                        'hg201':  roomMap_entry('HG00.201', set()),
                        'hg153':  roomMap_entry('HG00.153', set()),
                        'hg137':  roomMap_entry('HG00.137', set()),
                        'hg075':  roomMap_entry('HG00.075', set()),
                        'hg029':  roomMap_entry('HG00.029', set()),
                        'hg023':  roomMap_entry('HG00.023', set()),
                        'hgbib':  roomMap_entry('Bibliotheek', set()),
                        'hginfo': roomMap_entry('Infozuilen', set()),
                        'none':   roomMap_entry('Onbekend', set())}
        #  { <room>: [<event>, ...] }
        self._schedule = {}
        #  { <tag>: [<room-id>, ...] }
        self.tagMap = {'hg': set(['hg761', 'hg206', 'hg201', 'hg153',
                                  'hg137', 'hg075', 'hg029', 'hg023',
                                  'hgbib', 'hginfo'])}
        # versioning
        self.occupationVersion = 0
        self.roomMapVersion = 0
        self.scheduleVersion = 0
        self.tagMapVersion = 0
        # internal state
        self.pulling_schedule = False
        self.rooms_considered_for_schedule = None
        self.running = False
        # locks
        self.lock = threading.Lock()
        # Get occupation from history
        self.push_occupation_changes(self.history.get_occupation(), 'history',
                                        initial_history_push=True)
    def run(self):
        self.running = True
        self._pull_schedule_loop()
    def stop(self):
        self.running = False
    # Schedule polling routines
    # ###############################################################
    def _pull_schedule_loop(self):
        """ Called every 16 minutes to pull a new version of the schedule """
        try:
            self.pull_schedule()
            delay = 16*60
        except ScheduleError, e:
            self.l.exception("ScheduleError while pulling schedule.  "+
                             "Retrying in 5m")
            delay = 5*60
        if not self.running:
            return
        self.scheduler.plan(time.time() + delay, self._pull_schedule_loop)
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
                roomNames = [entry.name for entry in self.roomMap.values()]
                roomKeys = self.roomMap.keys()
                if not roomKeys:
                    return
                self.pulling_schedule = True
                roomMapVersion = self.roomMapVersion
            raw_schedule = self.schedule.fetch_todays_schedule(roomNames)
            with self.lock:
                self.pulling_schedule = False
                if roomKeys !=  self.roomMap.keys():
                    continue # rooms were changed in the meantime
                self.rooms_considered_for_schedule = roomKeys
                # Convert raw_schedule = { <roomName>: <events> }
                # into schedule = { <roomKey>: <events> }.
                schedule = {}
                for key, entry in self.roomMap.iteritems():
                    if entry.name not in raw_schedule:
                        continue
                    schedule[key] = raw_schedule[entry.name]
                # Did the schedule change?
                if schedule == self._schedule:
                    break # Nothing changed
                self.l.info("Pulled new schedule; version %s",
                            self.scheduleVersion)
                self._schedule = schedule
                self.scheduleVersion += 1
                scheduleVersion = self.scheduleVersion
            self._on_schedule_changed(schedule, scheduleVersion)
            break
    # Helper functions to apply a tag-filter
    # ###############################################################
    def _filter_schedule(self, schedule, _filter):
        ret = {}
        if _filter is None:
            return schedule
        rooms_in_filter = reduce(lambda x,y: x | self.tagMap[y], _filter, set())
        for room, events in schedule.iteritems():
            if room in rooms_in_filter:
                ret[room] = events
        return ret
    def _filter_roomMap(self, roomMap, _filter):
        ret = {}
        if _filter is None:
            return roomMap
        rooms_in_filter = reduce(lambda x,y: x | self.tagMap[y], _filter, set())
        for room, entry in roomMap.iteritems():
            if room in rooms_in_filter:
                ret[room] = entry
        return ret
    def _filter_occupation(self, occupation, _filter):
        ret = {}
        if _filter is None:
            return occupation
        rooms_in_filter = reduce(lambda x,y: x | self.tagMap[y], _filter, set())
        pcs_in_filter = reduce(lambda x,y: x | self.roomMap[y].pcs,
                                        rooms_in_filter, set()) 
        for pc, v in occupation.iteritems():
            if pc in pcs_in_filter:
                ret[pc] = v
        return ret
    # Functions to execute callbacks when roomMap/schedule/occ./... changes
    # ###############################################################
    def _on_schedule_changed(self, sched, scheduleVersion):
        listeners = copy(self.schedule_listeners)
        for _filter, callbacks in self.schedule_listeners.iteritems():
            filtered_sched = self._filter_schedule(sched, _filter)
            if filtered_sched:
                for callback in callbacks:
                    callback(filtered_sched, scheduleVersion)
    def _on_roomMap_changed(self, roomMap, roomMapVersion):
        listeners = copy(self.roomMap_listeners)
        for _filter, callbacks in self.roomMap_listeners.iteritems():
            filtered_roomMap = self._filter_roomMap(roomMap, _filter)
            if filtered_roomMap:
                for callback in callbacks:
                    callback(filtered_roomMap, roomMapVersion)
    def _on_occupation_changed(self, updates, source,
                                    occupationVersion):
        listeners = copy(self.occupation_listeners)
        for _filter, callbacks in self.occupation_listeners.iteritems():
            filtered_updates = self._filter_occupation(updates, _filter)
            if not filtered_updates:
                continue
            for callback in callbacks:
                callback(filtered_updates, source, occupationVersion)
    # Functions to register callbacks
    # ###############################################################
    def register_on_schedule_changed(self, cb, _filter=None):
        with self.lock:
            if _filter is not None:
                _filter = tuple(sorted(_filter))
            if not _filter in self.schedule_listeners:
                self.schedule_listeners[_filter] = set([])
            self.schedule_listeners[_filter].add(cb)
    def register_on_occupation_changed(self,cb, _filter=None):
        with self.lock:
            if _filter is not None:
                _filter = tuple(sorted(_filter))
            if not _filter in self.occupation_listeners:
                self.occupation_listeners[_filter] = set([])
            self.occupation_listeners[_filter].add(cb)
    def register_on_roomMap_changed(self, cb, _filter=None):
        with self.lock:
            if  _filter is not None:
                _filter = tuple(sorted(_filter))
            if not _filter in self.roomMap_listeners:
                self.roomMap_listeners[_filter] = set([])
            self.roomMap_listeners[_filter].add(cb)
    def unregister_on_schedule_changed(self, cb, _filter=None):
        with self.lock:
            if  _filter is not None:
                _filter = tuple(sorted(_filter))
            self.schedule_listeners[_filter].remove(cb)
    def unregister_on_occupation_changed(self, cb, _filter=None):
        with self.lock:
            if  _filter is not None:
                _filter = tuple(sorted(_filter))
            self.occupation_listeners[_filter].remove(cb)
    def unregister_on_roomMap_changed(self, cb, _filter=None):
        with self.lock:
            if  _filter is not None:
                _filter = tuple(sorted(_filter))
            self.roomMap_listeners[_filter].remove(cb)
    # Handle changes to occupation
    # ###############################################################
    def push_occupation_changes(self, occ, source='unknown',
                                    initial_history_push=False):
        roomMap_changed = False
        pull_new_schedule = False
        processed_occ = {}
        with self.lock:
            for pc, state in occ.iteritems():
                pc = pc.lower() # normalize HG075PC47 -> hg075pc47
                # update occupation
                if pc not in self.occupation or self.occupation[pc] != state:
                    processed_occ[pc] = state
                    self.occupation[pc] = state
                # to which room does this pc belong?
                if (pc.startswith('cz') or pc.endswith('docent') or
                        'pc' not in pc):
                    room = 'none'
                else:
                    # TODO do not hardcode this
                    room, pcBit = pc.split('pc')
                    room = {'bib': 'hgbib',
                            'info': 'hginfo'}.get(room, room)
                    if not room in self.roomMap:
                        self.l.warning('New room: %s', room)
                        self.roomMap[room] = roomMap_entry(room, set())
                        roomMap_changed = True
                if not pc in self.roomMap[room].pcs:
                    self.roomMap[room].pcs.add(pc)
                    roomMap_changed = True
            if roomMap_changed:
                self.roomMapVersion += 1
                roomMap = deepcopy(self.roomMap)
                if (self.rooms_considered_for_schedule != roomMap.keys() and
                        not self.pulling_schedule):
                    pull_new_schedule = True
        if roomMap_changed:
            self._on_roomMap_changed(roomMap, self.roomMapVersion)
        if processed_occ:
            self.occupationVersion += 1
            self._on_occupation_changed(processed_occ, source,
                                        self.occupationVersion)
            if not initial_history_push:
                self.history.record_occupation_updates(processed_occ,
                        source, self.occupationVersion)
        if pull_new_schedule and not initial_history_push:
            self.pull_schedule()
    # Data accessors
    # ###############################################################
    def get_occupation(self, _filter=None):
        with self.lock:
            return (self._filter_occupation(self.occupation, _filter),
                            self.occupationVersion)
    def get_roomMap(self, _filter=None):
        with self.lock:
            return (self._filter_roomMap(deepcopy(self.roomMap), _filter),
                            self.roomMapVersion)
    def get_schedule(self, _filter=None):
        with self.lock:
            return (self._filter_schedule(deepcopy(self._schedule), _filter),
                            self.scheduleVersion)
    def get_tagMap(self):
        with self.lock:
            return (deepcopy(self.tagMap), self.tagMapVersion)
