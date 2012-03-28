# vim: et:sta:bs=2:sw=4:

from mirte.core import Module

from joyce.base import JoyceChannel

def prepare_roomMap(roomMap):
    """ Prepares the roomMap to be JSONified. That is: convert the non
        JSON serializable objects such as set() """
    ret = {}
    for room in roomMap:
        ret[room] = [roomMap[room].name, list(roomMap[room].pcs)]
    return ret

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
        # Only send messages for rooms with one of these tags
        self.msgFilter = {'occupation': [],
                          'schedule': [],
                          'roomMap': []}
        self.send_message({
            'type': 'welcome',
            'protocols': [1]})
        self._send_tag_names()
    # Called after the channel has been closed
    # ###############################################################
    def after_close(self):
        for k, _filter in self.msgFilter.iteritems():
            self._unregister_listener(k, _filter)
    # Helpers to (un)register callbacks for changes
    # ###############################################################
    def _unregister_listener(self, event, _filter):
        if _filter == []:
            return
        if event == 'occupation':
            self.server.state.unregister_on_occupation_changed(
                    self._on_occupation_changed, _filter)
        elif event == 'schedule':
            self.server.state.unregister_on_schedule_changed(
                    self._on_schedule_changed, _filter)
        elif event == 'roomMap':
            self.server.state.unregister_on_roomMap_changed(
                    self._on_roomMap_changed, _filter)
    def _register_listener(self, event, _filter):
        if _filter == []:
            return
        if event == 'occupation':
            self.server.state.register_on_occupation_changed(
                    self._on_occupation_changed, _filter)
        elif event == 'schedule':
            self.server.state.register_on_schedule_changed(
                    self._on_schedule_changed, _filter)
        elif event == 'roomMap':
            self.server.state.register_on_roomMap_changed(
                    self._on_roomMap_changed, _filter)
    # Handle an incoming message
    # ###############################################################
    def handle_message(self, data):
        if data['type'] == 'set_msgFilter':
            tagMap = self.server.state.get_tagMap()[0]
            for k in ('occupation', 'schedule', 'roomMap'):
                if k not in data:
                    continue
                if isinstance(data[k], list):
                    tags = [x for x in data[k] if x in self.server.state.tagMap]
                elif data[k] is None:
                    tags = None
                else:
                    continue
                self._unregister_listener(k, self.msgFilter[k])
                self.msgFilter[k] = tags
                self._register_listener(k, self.msgFilter[k])
        elif data['type'] == 'get_occupation':
            self._send_occupation()
        elif data['type'] == 'get_roomMap':
            self._send_roomMap()
        elif data['type'] == 'get_schedule':
            self._send_schedule()
        elif data['type'] == 'get_tag_names':
            self._send_tag_names()
        elif data['type'] == 'get_tagMap':
            self._send_tagMap()
    def _send_tagMap(self):
        tagMap, version = self.server.state.get_tagMap()
        self.send_message({
            'type': 'tags',
            'version': version,
            'tags': tagMap})
    def _send_tag_names(self):
        tagMap, version = self.server.state.get_tagMap()
        self.send_message({
            'type': 'tags',
            'version': version,
            'tags': tagMap.keys()})
    def _send_schedule(self):
        schedule, version = self.server.state.get_schedule(
                                self.msgFilter['schedule'])
        self.send_message({
            'type': 'schedule',
            'version': version,
            'schedule': prepare_schedule(schedule)})
    def _on_schedule_changed(self, schedule, version):
        self.send_message({
            'type': 'schedule',
            'version': version,
            'schedule': prepare_schedule(schedule)})
    def _send_roomMap(self):
        roomMap, version = self.server.state.get_roomMap(
                                self.msgFilter['roomMap'])
        self.send_message({
            'type': 'roomMap',
            'version': version,
            'roomMap': prepare_roomMap(roomMap)})
    def _on_roomMap_changed(self, roomMap, version):
        self.send_message({
            'type': 'roomMap',
            'version': version,
            'roomMap': prepare_roomMap(roomMap)})
    def _send_occupation(self):
        occ, version = self.server.state.get_occupation(
                                self.msgFilter['occupation'])
        self.send_message({
            'type': 'occupation',
            'version': version,
            'occupation': occ})
    def _on_occupation_changed(self, updates, source, version):
        self.send_message({
            'type': 'occupation_update',
            'version': version,
            'update': updates})
        

class CometApi(Module):
    def __init__(self, *args, **kwargs):
        super(CometApi, self).__init__(*args, **kwargs)
        self.joyceServer.channel_class = self._channel_constructor
        self.state.on_tagMap_changed.register(self._on_tagMap_changed)
    def _channel_constructor(self, *args, **kwargs):
        return CometApiChannelClass(self, *args, **kwargs)
    def _on_tagMap_changed(self, tagMap, version):
        self.joyceServer.broadcast_message({
            'type': 'tagMap',
            'version': version,
            'tagMap': tagMap})
