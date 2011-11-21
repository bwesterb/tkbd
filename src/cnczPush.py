# vim: et:sta:bs=2:sw=4:

import json
from BaseHTTPServer import BaseHTTPRequestHandler

from mirte.core import Module

from sarah.socketServer import TCPSocketServer
from sarah.io import IntSocketFile

class CnczPushRHWrapper(object):
    """ Acts as glue between our derivation of BaseHTTPRequestHandler and
        the SocketServer """
    def __init__(self, request, addr, server, l):
        self.request = IntSocketFile(request)
        self.addr = addr
        self.server = server
        self.l = l
    def handle(self):
        self.h = CnczPushRH(self.request, self.addr, self.server, self.l)
    def interrupt(self):
        self.request.interrupt()
    def cleanup(self):
        pass

class CnczPushRH(BaseHTTPRequestHandler):
    def __init__(self, request, addr, server, l):
        self.l = l
        self.addr = addr
        self.server = server
        BaseHTTPRequestHandler.__init__(self, request, addr, server)

    def do_POST(self):
        # Lets check whether the request is proper
        if self.path != '/push':
            return self._respond_simple(500, "Path %s not ok" % repr(self.path))
        if not 'Content-Length' in self.headers:
            return self._respond_simple(500, "No Content-Length")
        # TODO we should add better authentication and not hardcode this
        if not self.addr[0] in ('127.0.0.1', '131.174.30.41',
                                    '131.174.16.130'):
            return self._respond_simple(403, "Permission denied")
        # Read, parse, mangle and pass through
        raw_data = self.rfile.read(int(self.headers['Content-Length']))
        data = json.loads(raw_data)
        occ = {}
        source = data.get('datasource', 'unknown')
        for pc, state in data['data'].iteritems():
            expect_session = True
            if 'event' in state:
                if state['event'] == 'logon':
                    s = 'u'
                elif state['event'] == 'logoff':
                    s = 'f'
            elif state['status'] == 'offline':
                s = 'o'
                expect_session = False
            elif state['status'] == 'free':
                s = 'f'
            elif state['status'] == 'used':
                s = 'u'
            elif state['status'] == 'unknown':
                s = 'x'
                expect_session = False
            if 'session' in state:
                if state['session'] == 'windows':
                    s = 'w' + s
                elif state['session'] == 'linux':
                    s = 'l' + s
            elif expect_session:
                s = 'w' + s # XXX
            occ[pc] = s
        self.server._push(occ, source)
        self.l.info("Pushed %s entries; source %s" % (len(data['data']),source))
        self._respond_simple(200, 'true')

    def _respond_simple(self, code, message):
        self.l.debug('_respond_simple: %s %s' % (code, repr(message)))
        self.send_response(code)
        self.end_headers()
        self.wfile.write(message)

    def log_message(self, format, *args, **kwargs):
        self.l.info(format, *args, **kwargs)
    def log_error(self, format, *args, **kwargs):
        self.l.error(format, *args, **kwargs)
    def log_request(self, code=None, size=None):
        self.l.info("Request: %s %s" % (code, size))

class CnczPush(TCPSocketServer):
    """ Listens for notification from C&CZ on port 1235 """
    def __init__(self, *args, **kwargs):
        super(CnczPush, self).__init__(*args, **kwargs)
    def create_handler(self, con, addr, logger):
        return CnczPushRHWrapper(con, addr, self, logger)
    def _push(self, occ, source):
        self.state.push_occupation_changes(occ, source)

