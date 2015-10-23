#!/usr/bin/python3

import pickle
import requests
import json
import config
import os
import imghdr
import urllib.request
import http.cookiejar

# from time import strftime

SIGNIN_URL = "https://connect.monstercat.com/signin"
COVER_ART_BASE = "https://connect.monstercat.com/img/labels/monstercat/albums/"
DATA_PATH = os.path.expanduser('~/.monstercatconnect/')
TMP_PATH = DATA_PATH + "tmp/"
SAVE_FILE = DATA_PATH + "save.tmp"
COOKIE_FILE = DATA_PATH + "connect.cookies"

TELEGRAM_API_BASE = "https://api.telegram.org/bot"


def main():
    create_directories()
    new = load_album_list()
    new_ids = get_album_ids(new)
    old_ids = get_album_ids(load_from_file(SAVE_FILE))
    new_items = list(set(new_ids) - set(old_ids))
    
    # write_to_file(SAVE_FILE, new)

    if len(new_items):
        print("NEW ITEMS!!")
        print(new_items)

        for album in new:
            if album.get("_id") in new_items:
                print(album.get("title", "NO TITLE") + " by " + album.get("renderedArtists",
                                                                          "NO ARTIST") + " [" + album.get("catalogId",
                                                                                                          "NO ID") + "]")
                cj, successful = load_cookies(COOKIE_FILE)
                save_picture(COVER_ART_BASE + album.get("coverArt"), TMP_PATH+"tmp_pic", cj)

                imgtype = imghdr.what(TMP_PATH+"tmp_pic")
                if imgtype is None:
                    print("Not a valid image, skipping!")
                    continue

                new_path = TMP_PATH + "pic" + "." + imgtype
                os.rename(TMP_PATH+"tmp_pic", new_path)
                print("Moved to " + new_path)

                send_photo(new_path, album.get("title", "NO TITLE") + " by " + album.get("renderedArtists",
                                                                          "NO ARTIST") + " [" + album.get("catalogId",
                                                                                                          "NO ID") + "]")
    else:
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
    os.makedirs(TMP_PATH, exist_ok=True)


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


def send_photo(photo_path, caption):
    print("Sending/uploading photo")
    files = {"photo": open(photo_path, "rb")}
    payload = {"chat_id": config.telegram['chat_id'], "caption": caption}
    response = requests.post(TELEGRAM_API_BASE + config.telegram['bot_token'] + "/" + "sendPhoto", files=files, data=payload)
    print(response.text)


def save_picture(url, path, cj):
    print("Saving picture "+url)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    r = opener.open(url)
    output = open(path, "wb")
    output.write(r.read())
    output.close()


if __name__ == '__main__':
    main()
