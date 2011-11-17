# vim: et:sta:bs=2:sw=4:
""" Module responsible for storing the state between processes and restarts.

    The state is currently stored encoded with msgpack in simple files with
    filelocking to keep installation simple and persistent and caching
    up-front to keep it quick.

    We might want to convert this to MongoDB. """

from django.conf import settings
from django.core.cache import cache

import json
import time
import os.path

import msgpack
from lockfile import FileLock

#
# Internals
# ######################################################################
def _lock(x):
    return FileLock(_path(x))

def _path(x):
    return os.path.join(settings.STATE_DIR, x)

def _set_simple(key, obj, acquire_lock=True):
    fn = '%s.msgpack' % key
    if acquire_lock:
        lock = _lock(fn)
        lock.acquire()
    try:
        cache.set('state-'+key, obj)
        with open(_path(fn), 'w') as f:
            f.write(msgpack.packb(obj))
    finally:
        if acquire_lock:
            lock.release()

def _get_simple(key, acquire_lock=True):
    ck = 'state-'+key
    ret = cache.get(ck)
    if ret is not None:
        return ret
    fn = '%s.msgpack' % key
    if acquire_lock:
        lock = _lock(fn)
        lock.acquire()
    try:
        try:
            with open(_path(fn), 'r') as f:
                ret = msgpack.unpackb(f.read())
        except IOError, e:
            if e.errno == 2: # No such file or directory
                ret = {}
        cache.set(ck, ret)
    finally:
        if acquire_lock:
            lock.release()
    return ret

#
# Functions
# ######################################################################

# TODO document

def set_occupation(occ, acquire_lock=True):
    _set_simple('occupation', occ, acquire_lock=acquire_lock)

def get_occupation(acquire_lock=True):
    return _get_simple('occupation', acquire_lock=acquire_lock)

def set_occupation_of(pc, state):
    set_occupation_of_multiple({pc: state})

def set_occupation_of_multiple(pc_to_states, source='unknown'):
    with _lock('occupation'):
        occ = get_occupation(acquire_lock=False)
        for pc, state in pc_to_states.items():
            if not pc in occ:
                occ[pc] = {}
            if state['status']:
                occ[pc]['status'] = state['status']
            if state['session']:
                occ[pc]['session'] = state['session']
        set_occupation(occ, acquire_lock=False)
    with _lock('history'):
        with open(_path('history.jsons'), 'a') as f:
            for pc, state in pc_to_states.items():
                f.write(json.dumps([source, time.time(), pc, state]))
                f.write("\n")

