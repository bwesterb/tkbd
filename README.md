tkbd
====
`tkbd` is a daemon run on the faculty of sciences of the
[Radboud University Nijmegen](http://ru.nl) to register
which computer lab PC's are free and which are taken.

[tkb.js](http://github.com/bwesterb/tkb.js) is a frontend.

How it works
------------
### Information stored
`tkbd` maintains three bits of information. See `state.py`.

1. *occupation*: for each PC its current state, which is either:
   - `o` the PC is turned off
   - `x` the PC is in an unknown state
   - `wf` the PC is free and booted in Windows
   - `lf` the PC is free and booted in Linux
   - `wu` the PC is used and booted in Windows 
   - `lu` the PC is used and booted in Linux
   - `wx` the PC is booted in Windows, but we do not know if it is used
   - `lx` the PC is booted in Linux, but we do not know if it is used
2. *roomMap*: a list of rooms and the PC's in it.
3. *schedule*: for each room, the possible reservations of it.
4. *tagMap*: a list of tags and the rooms belonging to each tag.
   For instance, in the `hg` tag (which is short for Huygens Gebouw)
   are all the rooms of the Huygens Gebouw.

### Source of information
When people log in and out of computers, this is logged.
A script watches the log and pushes changes to `tkbd` via
HTTP requests on port 1235. See `cnczPush.py`.

Secondly, another script periodically polls all PCs.
The results of this scan are also pushed to port 1235.

The schedule is pulled from [Ruuster](http://ruuster.nl).
See `ruuster.py`.

### How to access it
#### Joyce
`tkbd` uses a bidirectional JSON message exchanging protocol over HTTP
called Joyce.  A client can create many channels with the server.
On each of these channels, the server and the client can send messages
to eachother.

1. To create a channel, send a HTTP GET request to the server for `/?m=null`.
   The server wil respond with an array `[<token>, <messages>, <streams>]`.
   `token` contains the token assigned to this channel. `messages` is a list
   of messages the server has send. `streams` is not important for `tkbd`.
2. After this, you should send another HTTP GET request to the server. This
   time for `/?m=[<token>]`. This time the server might not respond immediately.
   When there is a message (or after a timeout), the server will
   respond with a similar array `[<token>, <messages>, <streams>]`.
3. To send a list of messages `messages`, send a HTTP GET request
   to the server for `/?m=[<token>, <messages>]`. Now there are two outstanding
   HTTP requests. The one to send these messages and another to receive.
   One of these two will be responded to immediately. The other will stay
   open to receive messages.

So, what messages does `tkbd` send and `tkbd` likes to receive?

#### Messages received by `tkbd`
These are the messages understood by `tkbd`.  See `cometApi.py`.

1. `{"type": "set_msgFilter", "schedule":filter1, "roomMap":filter2, "occupation":filter3}`

    When checking the occupation of PC's in the Huygens Gebouw, one is not interested
    occupation updates for PC's in other faculties.  When the server receives this
    message, it will set a message filter for the three types of messages.  A filter
    is either a list of tags to allow (eg. `["hg"]`) or `null` which means
    "do not filter".
    
    The default filters are all `[]`.  That is: all rooms and PC's are filtered out and
    thus no update is sent.
    
2. `{"type": "get_occupation"}`

    When received, the server will send in return an `occupation` message.
    (See below.)

3. `{"type": "get_roomMap"}`

    When received, the server will send in return a `roomMap` message.
    (See below.)

4. `{"type": "get_schedule"}`

    When received, the server will send in return a `schedule` message.
    (See below.)

5. `{"type": "get_tag_names"}`

    When received, the server will send in return a `tags` message. (See below.)

6. `{"type": "get_tagMap"}`

    When received, the server will send in return a `tagMap` message. (See below.)

7. `{"type": "get_historic_updates", "offset": <offset>, "count": <count>}`

    When received, the server will send in return a `historic_updates` message.
    (See below.)


#### Messages sent by `tkbd`
Every messages sent by `tkbd` is one of the following. See `cometApi.py`.

1. `{"type": "welcome", "protocols" : [1]}`

    This is the first message sent. It tells which protocols `tkbd` understands.
    Currently, there is only protocol supported: `1`.

2. `{"type": "occupation", "version": <version>, "occupation": <occupation>}`

    It contains the current occupation of PC's. `occupation` is a dictionary
    with as keys names of PC's and as values the state of the corresponding PC's.
    Only PC's are included that match the current `occupation` filter.
    (See `set_msgFilter`.)

3. `{"type": "roomMap", "version": <version>, "roomMap": <roomMap>}`

    `roomMap` is a dictionary with as keys names of rooms and as values the
    corresponding list of PC's in that room.  Only PC's are included that
    match the current `roomMap` filter. (See `set_msgFilter`.)

4. `{"type": "schedule", "version": <version>, "schedule": <schedule>}`

    `schedule` is a dictionary with as keys names of rooms and as values the
    corresponding schedule of that room.  A schedule of a room is a list of
    events.
    An event is a list with three element: the first element is the starting
    time; the second is the ending time and the third is a decription of
    the event.
    Only rooms are included that match the current `schedule` filter.
    (See `set_msgFilter`.)

5. `{"type": "occupation_update", "version": <version>, "update": <update>}`

    This  message is sent, when the occupation of one or more PCs changes.
    `update` is a dictionary with as keys PC names and as values the
    new state of the corresponding PC.
    Only updates are sent for PC's that match the current `occupation` filter.
    (See `set_msgFilter`.)

6.  `{"type": "tags", "tags": <tags>}`

    This is the second message sent.  `tags` is the list of tags.

7.  `{"type": "tagMap", "tagMap": <tagMap>}`

    `tagMap` is a dictionary with as keys names of tags and as values the
    corresponding list of rooms that have the tag.

8.  `{"type": "historic_updates", "count": <count>, "offset": <offset>, "updates": <updates>}`

    This gives `count` historic updates from the `offset`th one.
    `updates` is a list of quadrupels
    `[<pc>, <source>, <unix timestamp>, <occupation>]`.

On every update of the occupation, roomMap, tagMap or schedule, the
corresponding version is incremented by one.

How to install it
-----------------
The simplest way to install `tkbd` is to run

```
$ easy_install tkbd
```

`easy_install` is a part of Python's
[setuptools](http://pypi.python.org/pypi/setuptools).
(In Debian, try `apt-get install python-setuptools`).

How to run it
-------------
To run, simply execute:

```
$ mirte tkbd/setups/default
```

This will run the default setup of `tkbd`.  For changes in occupation
it will listen on port 1235.  This is not useful if you are not
the IT guys of the faculty. 

You can configure `tkbd` to mirror another `tkbd` instance.  To
mirror the default `tk.science.ru.nl`, simply run:

```
$ mirte tkbd/setups/slave
```

To create a custom configuration, copy and edit one of the `.mirte` files
in `src/setups`.

Changelog
---------
* 0.3.8:
   * state: handle schedule exceptions correctly
* 0.3.7:
   * ruuster: handle more exceptions gracefully
* 0.3.6:
   * Add get_historic_updates to API
* 0.3.5:
   * Some minor improvements and bugfixes in the history and mirror modules
* 0.3.4:
   * keep history of occupation updates in a SQQLite3 database
* 0.3.3:
   * mirror: support tags
   * ruuster: normalize event names
   * ruuster: handle errors more gracefully
* 0.3.2
   * Fix: do not crash on new schedule.
* 0.3.1
   * Fix: special `null' tag filter to disable filter is properly set
* 0.3.0
  * Feature: add tags.  This will allow multiple `screens' running on the
    same tkbd.
* 0.2.4
  * Fix: keep mirror running if master is down for a while
  * Fix: ignore PCs with names ending with `docent'
* 0.2.3
  * Fix: properly package .mirte files
  * Fix: send proper start and ending times for the scheduled events
* 0.2.0
  * Support for mirroring
  * Fix some bugs
