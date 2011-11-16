This is the website that is/will be used to show the usage of the
computer laboratories on the _Faculteit der Natuurwetenschappen, Wiskunde
en Informatica_ of _the Radboud Universiteit Nijmegen_.

Installation
------------

- Install the Python packages:
    - python-msgpack
    - BeautifulSoup
    - lockfile
- Copy `settings.example.py` to `settings.py` and change `SECRET_KEY` to
  something random and secret; `MEDIA_ROOT` to the path to the `/media` folder
  and `STATE_DIR` to an appropriate directory (eg. "/var/lib/tkb").
- Run `./manage.py runserver` to test the installation.
- Consult `./manage.py runfcgi --help` to run it properly.
