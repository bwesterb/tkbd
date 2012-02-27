# vim: et:sta:bs=2:sw=4:

from mirte.core import Module

from joyce.base import JoyceChannel

def prepare_schedule(schedule):
    """ Prepares the schedule to be JSONified. That is: convert the non
        JSON serializable objects such as the datetime.time's """
    ret = {}
    for room in schedule:
        ret[room] = []
        for event in schedule[room]:
            ret[room].append(((event[0].hour,
                                event[0].minute),
                             (event[1].hour,
                              event[1].minute),
                             event[2]))
    return ret

class CometApiChannelClass(JoyceChannel):
    def __init__(self, server, *args, **kwargs):
        super(CometApiChannelClass, self).__init__(*args, **kwargs)
        self.server = server
        self.send_message({
            'type': 'welcome',
            'protocols': [0]})
        self._send_roomMap()
        self._send_occupation()
        self._send_schedule()

    def handle_message(self, data):
        if data['type'] == 'get_occupation':
            self._send_occupation()
        elif data['type'] == 'get_roomMap':
            self._send_roomMap()
    def _send_schedule(self):
        schedule, version = self.server.state.get_schedule()
        self.send_message({
            'type': 'schedule',
            'version': version,
            'schedule': prepare_schedule(schedule)})
    def _send_roomMap(self):
        roomMap, version = self.server.state.get_roomMap()
        self.send_message({
            'type': 'roomMap',
            'version': version,
            'roomMap': roomMap})
    def _send_occupation(self):
        occ, version = self.server.state.get_occupation()
        self.send_message({
            'type': 'occupation',
            'version': version,
            'occupation': occ})
        

class CometApi(Module):
    def __init__(self, *args, **kwargs):
        super(CometApi, self).__init__(*args, **kwargs)
        self.joyceServer.channel_class = self._channel_constructor
        self.state.on_roomMap_changed.register(self._on_roomMap_changed)
        self.state.on_occupation_changed.register(self._on_occupation_changed)
        self.state.on_schedule_changed.register(self._on_schedule_changed)
    def _channel_constructor(self, *args, **kwargs):
        return CometApiChannelClass(self, *args, **kwargs)
    def _on_schedule_changed(self, schedule, version):
        self.joyceServer.broadcast_message({
            'type': 'schedule',
            'version': version,
            'schedule': prepare_schedule(schedule)})
    def _on_roomMap_changed(self, roomMap, version):
        self.joyceServer.broadcast_message({
            'type': 'roomMap',
            'version': version,
            'roomMap': roomMap})
    def _on_occupation_changed(self, occ, source, version):
        self.joyceServer.broadcast_message({
            'type': 'occupation_update',
            'version': version,
            'update': occ})
