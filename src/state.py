# vim: et:sta:bs=2:sw=4:

import threading

from mirte.core import Module
from sarah.event import Event

class State(Module):
    def __init__(self, *args, **kwargs):
        super(State, self).__init__(*args, **kwargs)
        self.on_occupation_changed = Event()
        self.on_roomMap_changed = Event()
        self.occupation = {}
        self.roomMap = {}
        self.version = 0
        self.lock = threading.Lock()
    def push_occupation_changes(self, occ, source='unknown'):
        roomMap_changed = False
        with self.lock:
            self.version += 1
            for pc, state in occ.iteritems():
                # TODO do not hardcode this
                if pc.startswith('cz'):
                    continue
                self.occupation[pc] = state
                # TODO pull roomMap from ethergids instead of using these
                # heuristics
                roomBit, pcBit = pc.split('pc')
                room = {'hg761': 'HG03.761',
                    'hg206': 'HG02.206',
                    'hg201': 'HG00.201',
                    'hg153': 'HG00.153',
                    'hg137': 'HG00.137',
                    'hg075': 'HG00.075',
                    'hg029': 'HG00.029',
                    'hg023': 'HG00.023',
                    'bib': 'Library of Science',
                    'info': 'Infozuilen'}.get(roomBit, roomBit)
                if not room in self.roomMap:
                    self.roomMap[room] = []
                    roomMap_changed = True
                if not pc in self.roomMap[room]:
                    self.roomMap[room].append(pc)
                    roomMap_changed = True
            if roomMap_changed:
                roomMap = dict(self.roomMap)
            version = self.version
        if roomMap_changed:
            self.on_roomMap_changed(roomMap, version)
        self.on_occupation_changed(occ, source, version)
    def get_occupation(self):
        with self.lock:
            return (dict(self.occupation), self.version)
    def get_roomMap(self):
        with self.lock:
            return (dict(self.roomMap), self.version)
