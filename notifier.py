#!/usr/bin/python3

import json
import os
import pickle
import sys
import urllib.request
from pprint import pprint
from time import strftime

import requests

from config import telegram

API_PREFIX = "https://connect.monstercat.com/v2"
RELEASE_API_URL = API_PREFIX + "/catalog/browse"
# RELEASE_API_URL = "http://localhost:8080/browse"
COVER_URL = API_PREFIX + "/release/{}/cover?image_width=2048"
DATA_PATH = os.path.expanduser('~/.monstercatconnect/')
TMP_PATH = DATA_PATH + "tmp/"
IMG_FILE = TMP_PATH + "tmp_pic"
SAVE_FILE = DATA_PATH + "connect.db"
LOG_FILE = DATA_PATH + "output.log"

TELEGRAM_API_BASE = "https://api.telegram.org/bot" + telegram['bot_token'] + "/"

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
        for result in new.get("results"):
            if result.get("id") in new_items:
                release = result.get("release")
                message = "\"" + release.get("title", "NO TITLE") + \
                          "\" by \"" + release.get("artistsTitle", "NO ARTIST") + \
                          "\" [" + release.get("catalogId", "NO ID") + "]"
                log(message + " (" + result.get("id") + ")")

                cover_url = COVER_URL.format(release.get("id"))
                save_picture(cover_url, IMG_FILE)

                # FIXME imghdr doesn't detect jpeg with ffd8ffdb header
                # imgtype = imghdr.what(IMG_FILE)
                imgtype = "jpeg"
                if imgtype is None:
                    log("Not a valid image - just sending the message.")
                    send_message(message)
                    continue

                new_path = TMP_PATH + release.get("catalogId", "pic") + "." + imgtype
                os.rename(IMG_FILE, new_path)
                log("Moved to " + new_path)

                if os.path.getsize(new_path) > 10000000:  # if the pic is larger than 10 MB
                    log("Image is bigger than 10MB - size is: " + str(os.path.getsize(new_path)))

                    if os.path.getsize(new_path) > 50000000:  # if the pic is larger than 50 MB
                        log("Sending as message (>50MB).")
                        send_message(message)  # just send a message not the pic
                    else:
                        log("Sending as document (10MB-50MB).")
                        send_document(new_path, message)

                else:
                    # Send as photo if under 10MB
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
        album_ids.append(album.get("id"))

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
    payload = {"chat_id": telegram['chat_id'], "text": message}

    # response = \
    requests.post(requesturl, data=payload)
    # log(response.text)
    return


def send_photo(photo_path, caption):
    if "test" in sys.argv:
        return
    log("Sending photo")
    files = {"photo": open(photo_path, "rb")}
    payload = {"chat_id": telegram['chat_id'], "caption": caption}
    response_raw = requests.post(TELEGRAM_API_BASE + "sendPhoto", files=files, data=payload)
    response = json.loads(response_raw.text)
    if not response.get("ok"):
        raise Exception("Telegram-Error: " + str(response.get("error_code")) + " - " + response.get("description"))
    log("Send successful")


def send_document(document_path, caption):
    if "test" in sys.argv:
        return
    log("Sending document")
    files = {"document": open(document_path, "rb")}
    payload = {"chat_id": telegram['chat_id'], "caption": caption}
    response_raw = requests.post(TELEGRAM_API_BASE + "sendDocument", files=files, data=payload)
    response = json.loads(response_raw.text)
    if not response.get("ok"):
        raise Exception("Telegram-Error: " + str(response.get("error_code")) + " - " + response.get("description"))
    log("Send successful")


def save_picture(url, path):
    log("Saving picture " + url)
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
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
