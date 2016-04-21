#!/usr/bin/python3

import pickle
import requests
import json
import config
import os
import imghdr
import urllib.request
import sys
from time import strftime
from pprint import pprint

SIGNIN_URL = "https://connect.monstercat.com/signin"
COVER_ART_BASE = "https://s3.amazonaws.com/data.monstercat.com/blobs/"
RELEASE_API_URL = "https://connect.monstercat.com/api/catalog/release"
# RELEASE_API_URL = "http://localhost/connect"
DATA_PATH = os.path.expanduser('~/.monstercatconnect/')
TMP_PATH = DATA_PATH + "tmp/"
IMG_FILE = TMP_PATH + "tmp_pic"
SAVE_FILE = DATA_PATH + "connect.db"
LOG_FILE = DATA_PATH + "output.log"

TELEGRAM_API_BASE = "https://api.telegram.org/bot" + config.telegram['bot_token'] + "/"

# temp
LOG = sys.__stdout__

REMOVED_COOKIE_FILE = False


class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = LOG

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()


def main():
    create_directories()
    global LOG
    LOG = open(LOG_FILE, "a")

    log("------ BEGIN MONSTERCATCONNECTNOTIFIER ------")

    # based on http://stackoverflow.com/a/616672/3527128
    sys.stderr = Logger()

    new = load_album_list()
    new_ids = get_album_ids(new)
    old_ids = load_from_file(SAVE_FILE)
    new_items = list(set(new_ids) - set(old_ids))

    if len(new_items) and not len(new_items) > 20:
        log("New items!")
        for album in new.get("results"):
            if album.get("_id") in new_items:
                message = "\"" + album.get("title", "NO TITLE") + "\" by \"" + album.get("renderedArtists",
                                                                                         "NO ARTIST") + "\" [" + album.get(
                    "catalogId", "NO ID") + "]"
                log(message + " (" + album.get("_id") + ")")

                if album.get("imageHashSum") is None:
                    send_message(message)
                    continue
                save_picture(COVER_ART_BASE + album.get("imageHashSum"), IMG_FILE)

                imgtype = imghdr.what(IMG_FILE)
                if imgtype is None:
                    log("Not a valid image, skipping!")
                    continue

                new_path = TMP_PATH + "pic" + "." + imgtype
                os.rename(IMG_FILE, new_path)
                log("Moved to " + new_path)

                send_photo(new_path, message)
    elif len(new_items):
        log("Too many new items (> 20), skipping them.")
    else:
        log("No new song!")

    # write to file if everything worked (no exceptions etc)
    write_to_file(SAVE_FILE, new_ids)


def load_album_list():
    session = requests.Session()

    # GET ALBUM LIST
    log("Loading album list...")
    albums_raw = session.get(RELEASE_API_URL)

    # Sometimes the response is empty?
    if albums_raw is None or albums_raw.text is None:
        pprint(vars(albums_raw))
        raise Exception("albums_raw or albums_raw.text is None!")

    # PARSE RESPONSE INTO JSON
    albums = json.loads(albums_raw.text)
    return albums


def get_album_ids(albums):
    album_ids = []
    for album in albums.get("results"):
        album_ids.append(album.get("_id"))

    return album_ids


def create_directories():
    os.makedirs(DATA_PATH, exist_ok=True)
    os.makedirs(TMP_PATH, exist_ok=True)


def write_to_file(filename, list_to_save):
    log("Saving data to file...")
    with open(filename, 'wb') as f:
        pickle.dump(list_to_save, f)


def load_from_file(filename):
    log("Loading data from file...")
    if not os.path.isfile(filename):
        return []
    with open(filename, 'rb') as f:
        return pickle.load(f)


def send_message(message):
    if "test" in sys.argv:
        return
    log("Sending message")
    requesturl = TELEGRAM_API_BASE + "sendMessage"
    payload = {"chat_id": config.telegram['chat_id'], "text": message}

    # response = \
    requests.post(requesturl, data=payload)
    # log(response.text)
    return


def send_photo(photo_path, caption):
    if "test" in sys.argv:
        return
    log("Sending photo")
    files = {"photo": open(photo_path, "rb")}
    payload = {"chat_id": config.telegram['chat_id'], "caption": caption}
    response_raw = requests.post(TELEGRAM_API_BASE + "sendPhoto", files=files, data=payload)
    response = json.loads(response_raw.text)
    if not response.get("ok"):
        raise Exception("Telegram-Error: " + str(response.get("error_code")) + " - " + response.get("description"))
    log("Send successful")


def save_picture(url, path):
    log("Saving picture " + url)
    opener = urllib.request.build_opener()
    r = opener.open(urllib.request.quote(url, safe="%/:=&?~#+!$,;'@()*[]"))
    output = open(path, "wb")
    output.write(r.read())
    output.close()


def log(message):
    if "cron" not in sys.argv:
        print("[" + strftime("%Y-%m-%d %H:%M:%S") + "] " + message)
    LOG.write("[" + strftime("%Y-%m-%d %H:%M:%S") + "] " + message + "\n")


if __name__ == '__main__':
    main()
