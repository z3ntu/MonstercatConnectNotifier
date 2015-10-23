#!/usr/bin/python3

import pickle
import requests
import json
import config
import os
import collections
import http.cookiejar
# from time import strftime

SIGNIN_URL = "https://connect.monstercat.com/signin"
DATA_PATH = os.path.expanduser('~/.monstercatconnect/')
SAVE_FILE = DATA_PATH + "save.tmp"
COOKIE_FILE = DATA_PATH + "connect.cookies"

TELEGRAM_API_BASE = "https://api.telegram.org/bot"


def main():
    create_directories()
    new = load_album_list()
    new_ids = get_album_ids(new)
    old_ids = load_from_file(SAVE_FILE)
    new_items = list(set(new_ids) - set(old_ids))
    if len(new_items):
        print("NEW ITEMS!!")
        print(new_items)
        # send_message("There is a new song!")
        # write_to_file(SAVE_FILE, new)
        for album in new:
            if album.get("_id") in new_items:
                print(album.get("title", "NO TITLE") + " by " + album.get("renderedArtists", "NO ARTIST") + " [" + album.get("catalogId", "NO ID") + "]")
    else:
        # send_message("No new song!")
        print("No new song!")


def load_album_list():
    session = requests.Session()

    cj, successful = load_cookies(COOKIE_FILE)
    session.cookies = cj
    if not successful:
        # SIGN IN
        print("Logging in.")
        sign_in(session)
        save_cookies(session.cookies, COOKIE_FILE)

    # GET ALBUM LIST
    print("Loading album list...")
    albums_raw = session.get("https://connect.monstercat.com/albums")
    # albums_raw = session.get("http://localhost/connect")

    # PARSE RESPONSE INTO JSON
    albums = json.loads(albums_raw.text)
    return albums


def get_album_ids(albums):
    album_ids = []

    for album in albums:
        album_ids.append(album.get("_id"))

    return album_ids


def sign_in(session):
    payload = {"email": config.connect['email'], "password": config.connect['password']}
    print("Signing in...")
    session.post(SIGNIN_URL, data=payload)


def create_directories():
    print("Creating directories...")
    os.makedirs(DATA_PATH, exist_ok=True)


def write_to_file(filename, list_to_save):
    print("Saving data to file...")
    with open(filename, 'wb') as f:
        pickle.dump(list_to_save, f)


def load_from_file(filename):
    print("Loading data from file...")
    if not os.path.isfile(filename):
        return []
    with open(filename, 'rb') as f:
        return pickle.load(f)


def save_cookies_old(filename, session):
    with open(filename, 'w') as f:
        pickle.dump(requests.utils.dict_from_cookiejar(session.cookies), f)


def save_cookies(cj, filename):
    cj.save(filename=filename)


def load_cookies(filename):
    cj = http.cookiejar.MozillaCookieJar()
    if not os.path.isfile(filename):
        return cj, False
    cj.load(filename=filename)
    return cj, True


def send_message(message):
    requesturl = TELEGRAM_API_BASE + config.telegram['bot_token'] + "/" + "sendMessage"
    payload = {"chat_id": config.telegram['chat_id'], "text": message}

    response = requests.post(requesturl, data=payload)
    print(response.text)
    return

if __name__ == '__main__':
    main()
