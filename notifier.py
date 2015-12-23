#!/usr/bin/python3

import pickle
import requests
import json
import config
import os
import imghdr
import urllib.request
import http.cookiejar
import sys
from time import strftime

SIGNIN_URL = "https://connect.monstercat.com/signin"
COVER_ART_BASE = "https://connect.monstercat.com/img/labels/monstercat/albums/"
DATA_PATH = os.path.expanduser('~/.monstercatconnect/')
TMP_PATH = DATA_PATH + "tmp/"
IMG_FILE = TMP_PATH + "tmp_pic"
SAVE_FILE = DATA_PATH + "save.tmp"
COOKIE_FILE = DATA_PATH + "connect.cookies"
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
        # log(new_items)
        for album in new:
            if album.get("_id") in new_items:
                message = "\"" + album.get("title", "NO TITLE") + "\" by \"" + album.get("renderedArtists",
                    "NO ARTIST") + "\" [" + album.get("catalogId", "NO ID") + "]"
                log(message)
                cj, successful = load_cookies(COOKIE_FILE)
                if album.get("coverArt") is None:
                    send_message(message)
                    continue
                save_picture(COVER_ART_BASE + album.get("coverArt"), IMG_FILE, cj)

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

    cj, successful = load_cookies(COOKIE_FILE)
    session.cookies = cj
    session.headers = {'user-agent': 'github.com/z3ntu/MonstercatConnectNotifier'}
    if not successful:
        # SIGN IN
        log("Logging in.")
        sign_in(session)
        save_cookies(session.cookies, COOKIE_FILE)

    # GET ALBUM LIST
    log("Loading album list...")
    albums_raw = session.get("https://connect.monstercat.com/albums")
    # albums_raw = session.get("http://84.114.30.55/connect")

    # PARSE RESPONSE INTO JSON
    albums = json.loads(albums_raw.text)
    try:
        if albums['error']:
            global REMOVED_COOKIE_FILE
            if not REMOVED_COOKIE_FILE:
                log("Fatal error! Maybe because of expired cookies, deleting cookie file and retrying.")
                os.remove(COOKIE_FILE)
                REMOVED_COOKIE_FILE = True
                main()
                sys.exit(0)
            else:
                raise Exception("FATAL ERRROR! : " + str(albums))
    except TypeError:
        pass
    return albums


def get_album_ids(albums):
    album_ids = []
    for album in albums:
        album_ids.append(album.get("_id"))

    return album_ids


def sign_in(session):
    log("Signing in...")
    payload = {"email": config.connect['email'], "password": config.connect['password']}
    response_raw = session.post(SIGNIN_URL, data=payload)
    response = json.loads(response_raw.text)
    if len(response) > 0:
        log("Sign in failed")
        raise Exception("Sign-In Error: " + response.get("message", "Unknown error"))


def create_directories():
    # log("Creating directories...")
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


def save_cookies(cj, filename):
    log("Saving cookies")
    cj.save(filename=filename)


def load_cookies(filename):
    log("Loading cookies")
    cj = http.cookiejar.MozillaCookieJar()
    if not os.path.isfile(filename):
        return cj, False
    cj.load(filename=filename)
    return cj, True


def send_message(message):
    if "test" in sys.argv:
        return
    log("Sending message")
    requesturl = TELEGRAM_API_BASE + "sendMessage"
    payload = {"chat_id": config.telegram['chat_id'], "text": message}

    response = requests.post(requesturl, data=payload)
    log(response.text)
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


def save_picture(url, path, cj):
    log("Saving picture " + url)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
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
