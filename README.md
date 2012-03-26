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

#### Messages sent by `tkbd`
Every messages sent by `tkbd` is one of the following. See `cometApi.py`.

1. `{"type": "welcome", "protocols" : [0]}`

    This is the first message sent. It tells which protocols `tkbd` understands.
    Currently, there is only protocol: `0`.

2. `{"type": "occupation", "version": <version>, "occupation": <occupation>}`

    This is one of the first messages sent.  It contains the current
    occupation of PC's. `occupation` is a dictionary with as keys names of
    PC's and as values the state of the corresponding PC's.

3. `{"type": "roomMap", "version": <version>, "roomMap": <roomMap>}`

    This is one of the first messages sent. `roomMap` is a dictionary
    with as keys names of rooms and as values the corresponding list
    of PC's in that room.

4. `{"type": "schedule", "version": <version>, "schedule": <schedule>}`

    This is one of the first messages sent. `schedule` is a dictionary
    with as keys names of rooms and as values the corresponding
    schedule of that room.  A schedule of a room is a list of events.
    An event is a list with three element: the first element is the starting
    time; the second is the ending time and the third is a decription of
    the event.

5. `{"type": "occupation_update", "version": <version>, "update": <update>}`

    This  message is sent, when the occupation of one or more PCs changes.
    `update` is a dictionary with as keys PC names and as values the
    new state of the corresponding PC.

On every update of the occupation, roomMap or schedule, the corresponding
version is incremented by one.  A client should check whether
it has missed an update.  And if so, resynchronize by using one of
the following.

#### Messages received by `tkbd`
1. `{"type": "get_occupation"}`

    When received, the server will send in return an `occupation` message.

2. `{"type": "get_roomMap"}`

    When received, the server will send in return a `roomMap` message.

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
