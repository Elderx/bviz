## Install
1. git clone https://github.com/Elderx/bviz.git
2. cd bviz/
3. python3 -m venv venv
4. source venv/bin/activate
5. pip install -r requirements.txt

## Running
1. python3 main.py
2. python3 streamer.py

## Info

Client done with Raylib (https://www.raylib.com/). Draws Stuff(TM) on screen based on events coming from Bluesky Jetstream API (https://github.com/bluesky-social/jetstream).
streamer.py will connect to Jetstream API, parse JSON and filter it based on user input:
  --filter-text stuff
  --filter-lang en,fi,se (comma separated list of languages, will match on ANY)
