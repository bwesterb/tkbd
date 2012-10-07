import time
import sqlite3
import threading

from mirte.core import Module

class Sqlite3History(Module):
    def __init__(self, *args, **kwargs):
        super(Sqlite3History, self).__init__(*args, **kwargs)
        self.l.info("Opening database...")
        self.conn = sqlite3.connect(self.db, check_same_thread=False)
        self.pc2id_lut = dict()
        self.source2id_lut = dict()
        self.id2pc_lut = dict()
        self.id2source_lut = dict()
        self.lock = threading.Lock()  # lock for the database connection
        # New records are not INSERTed immediately, but are deferred to
        # a worker thread to increarse performance.
        self.recordCond = threading.Condition()
        self.recordQueue = []
        # Create tables and indexes if they do not already exist
        c = self.conn.cursor()
        c.execute(""" CREATE TABLE IF NOT EXISTS sources
                        ( id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
                          name STRING ) """)
        c.execute(""" CREATE UNIQUE INDEX IF NOT EXISTS name ON sources
                        ( name ) """)
        c.execute(""" CREATE TABLE IF NOT EXISTS pcs
                        ( id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
                          name STRING ) """)
        c.execute(""" CREATE UNIQUE INDEX IF NOT EXISTS name ON pcs
                        ( name ) """)
        c.execute(""" CREATE TABLE IF NOT EXISTS occupationUpdates
                        ( id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
                          pc INTEGER REFERENCES pcs ( id ),
                          source INTEGER REFERENCES sources ( id ),
                          datetime INTEGER,
                          occupation STRING) """)
        c.execute(""" CREATE INDEX IF NOT EXISTS pc_datetime
                            ON occupationUpdates
                                ( pc, datetime ) """)
        self.conn.commit()
        # Fetch the pc-name to pc-identifier table (and reverse)
        c.execute(""" SELECT id, name FROM pcs """)
        for _id, name in c:
            self.pc2id_lut[name] = _id
            self.id2pc_lut[_id] = name
        # Fetch the source-name to source-identifier table (and reverse)
        c.execute(""" SELECT id, name FROM sources """)
        for _id, name in c:
            self.source2id_lut[name] = _id
            self.id2source_lut[_id] = name
        # Fetch the number of updates
        c.execute(""" SELECT COUNT(*) FROM occupationUpdates """)
        n_updates = c.fetchone()[0]
        self.c = c
        self.l.info("  ... done: %s pcs %s sources %s updates",
                    len(self.pc2id_lut), len(self.source2id_lut), n_updates)

    def _id_for_pc(self, name):
        """ Given the name of the PC, return the database identifier. """
        if not name in self.pc2id_lut:
            self.c.execute("INSERT INTO pcs (name) VALUES ( ? )", (name,))
            self.pc2id_lut[name] = self.c.lastrowid
            self.id2pc_lut[self.c.lastrowid] = name
        return self.pc2id_lut[name]
    def _id_for_source(self, name):
        """ Given the name of the source, return the database identifier. """
        if not name in self.source2id_lut:
            self.c.execute("INSERT INTO sources (name) VALUES ( ? )", (name,))
            self.source2id_lut[name] = self.c.lastrowid
            self.id2source_lut[self.c.lastrowid] = name
        return self.source2id_lut[name]

    def get_occupation(self):
        """ Returns the occupation as was last recorded. """
        ret = {}
        self.l.info("Reading occupation from database...")
        with self.lock:
            for pc_name, pc_id in self.pc2id_lut.iteritems():
                self.c.execute(""" SELECT occupation FROM occupationUpdates
                                          WHERE pc=? ORDER BY datetime DESC
                                          LIMIT 0, 1 """, 
                                            (pc_id,))
                row = self.c.fetchone()
                if row is not None:
                    ret[pc_name] = row[0]
        self.l.info("  ... done: %s entries", len(ret))
        return ret

    def record_occupation_updates(self, updates, source, version):
        """ Records an occupation update """
        now = int(time.time())
        # Put it on the recordQueue and notify the worker thread.
        with self.recordCond:
            self.recordQueue.append((now, updates, source))
            self.recordCond.notify()

    def get_occupation_updates(self, offset=0, count=1000):
        """ Returns <count> occupation updates from <offset>.
        
            An occupation update is a quadrupel

                (pc, source, timestamp, occupation) """
        ret = []
        c = self.conn.cursor()
        for pc_id, source_id, datetime, occupation in c.execute(
                    """ SELECT pc, source, datetime, occupation
                            FROM occupationUpdates LIMIT ?, ? """,
                            (offset, count)):
            ret.append((self.id2pc_lut[pc_id],
                        self.id2source_lut[source_id],
                        datetime,
                        occupation))
        return ret

    def stop(self):
        with self.recordCond:
            self.running = False
            self.recordCond.notify()

    def run(self):
        """ Runs the worker thread that records occupation updates to the
            database. """
        # TODO is a separate thread necessary?  Wouldn't a threadPool.execute
        #      suffice?
        self.running = True
        self.recordCond.acquire()
        while self.running or self.recordQueue:
            # Check for new entries.  If none: wait.
            if self.running and not self.recordQueue:
                self.recordCond.wait()
                continue
            entries = list(reversed(self.recordQueue))
            self.recordQueue = []
            self.recordCond.release()
            with self.lock:
                # Record the entries
                for now, updates, source in entries:
                    for pc, occupation in updates.iteritems():
                        self.c.execute(""" INSERT INTO occupationUpdates
                                            ( pc, datetime, occupation, source )
                                           VALUES ( ?, ?, ?, ? ) """, (
                                   self._id_for_pc(pc), now, occupation,
                                   self._id_for_source(source)))
                self.conn.commit()
            self.recordCond.acquire()
        self.recordCond.release()

# vim: et:sta:bs=2:sw=4:
