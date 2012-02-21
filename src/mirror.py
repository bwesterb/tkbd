# vim: et:sta:bs=2:sw=4:

from mirte.core import Module

from joyce.base import JoyceChannel
from joyce.comet import CometJoyceClient

class MirrorChannelClass(JoyceChannel):
    def __init__(self, server, *args, **kwargs):
        super(MirrorChannelClass, self).__init__(*args, **kwargs)
        self.server = server
        self.msg_map = {
                'occupation': self._msg_occupation,
                'occupation_update': self._msg_occupation_update }
    def handle_message(self, data):
        typ = data.get('type')
        if typ in self.msg_map:
            self.msg_map[typ](data)
    def _msg_occupation(self, data):
        self.server.state.push_occupation_changes(data['occupation'])
    def _msg_occupation_update(self, data):
        self.server.state.push_occupation_changes(data['update'])
        
class Mirror(CometJoyceClient):
    def __init__(self, *args, **kwargs):
        super(Mirror, self).__init__(*args, **kwargs)
        self.channel_class = self._channel_constructor
    def _channel_constructor(self, *args, **kwargs):
        return MirrorChannelClass(self, *args, **kwargs)
    def run(self):
        # NOTE we assume CometJoyceClient.run returns immediately
        super(Mirror, self).run()
        self.channel = self.create_channel()
