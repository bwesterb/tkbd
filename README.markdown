This is the website that is/will be used to show the usage of the
computer laboratories on the _Faculteit der Natuurwetenschappen, Wiskunde
en Informatica_ of _the Radboud Universiteit Nijmegen_.

Installation
------------

- Install the Python packages `python-msgpack` and `BeatifulSoup`.
- Copy `settings.example.py` to `settings.py` and change `SECRET_KEY` to
  something random and secret; and `MEDIA_ROOT` to the path to
  the `/media` folder.
- Run `./manage.py runserver` to test the installation.
- Consult `./manage.py runfcgi --help` to run it properly.
