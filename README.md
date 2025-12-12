ytmndd - ytmnd downloader
=====

An updated ytmnd scraper based on [https://github.com/julescarbon/ytmnd](https://github.com/julescarbon/ytmnd)

`./ytmndd.py -u [username]`

`./ytmndd.py [domain]`

serving
-------

this scraper will download the gif and mp3 from a ytmnd and write a file embedding these things in addition to zoom text (if any).

The downloaded files cannot be loaded from a `file://` url. In order to view these files, put them online or run a local server. For example, `python -m http.server` from the directory and got to [http://localhost:8000/](http://localhost:8000/)

options
-------

| flag | description |
| -------------- | ----------------------- |
| `--user` (or `-u`) | fetch all ytmnds for a user |
| `--media-only`   | only download the gif and mp3 |
| `--html-only`    | only write an html file|
| `--json-only`    | writes simplified json to a file |
| `--no-web-audio` | uses the <audio> tag instead of web audio |
| `--print-json`   | dumps raw json from ytmnd to stdout |
