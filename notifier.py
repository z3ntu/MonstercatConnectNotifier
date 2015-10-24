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
IMG_FILE = TMP_PATH + "tmp_pic"
SAVE_FILE = DATA_PATH + "save.tmp"
COOKIE_FILE = DATA_PATH + "connect.cookies"

TELEGRAM_API_BASE = "https://api.telegram.org/bot" + config.telegram['bot_token'] + "/"


def main():
    create_directories()
    new = load_album_list()
    new_ids = get_album_ids(new)
    old_ids = get_album_ids(load_from_file(SAVE_FILE))
    new_items = list(set(new_ids) - set(old_ids))

    # write_to_file(SAVE_FILE, new)

    if len(new_items):
        print("New items!")
        print(new_items)

        for album in new:
            if album.get("_id") in new_items:
                print(album.get("title", "NO TITLE") + " by " + album.get("renderedArtists",
                                                                          "NO ARTIST") + " [" + album.get("catalogId",
                                                                                                          "NO ID") + "]")
                cj, successful = load_cookies(COOKIE_FILE)
                save_picture(COVER_ART_BASE + album.get("coverArt"), IMG_FILE, cj)

                imgtype = imghdr.what(IMG_FILE)
                if imgtype is None:
                    print("Not a valid image, skipping!")
                    continue

                new_path = TMP_PATH + "pic" + "." + imgtype
                os.rename(IMG_FILE, new_path)
                print("Moved to " + new_path)

                send_photo(new_path, "\"" + album.get("title", "NO TITLE") + "\" by \"" + album.get("renderedArtists",
                                                                          "NO ARTIST") + "\" [" + album.get("catalogId",
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
    print("Signing in...")
    payload = {"email": config.connect['email'], "password": config.connect['password']}
    response_raw = session.post(SIGNIN_URL, data=payload)
    response = json.loads(response_raw.text)
    if len(response) > 0:
        print("Sign in failed")
        raise Exception("Sign-In Error: " + response.get("message", "Unknown error"))


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


def save_cookies(cj, filename):
    print("Saving cookies")
    cj.save(filename=filename)


def load_cookies(filename):
    print("Loading cookies")
    cj = http.cookiejar.MozillaCookieJar()
    if not os.path.isfile(filename):
        return cj, False
    cj.load(filename=filename)
    return cj, True


def send_message(message):
    print("Sending message")
    requesturl = TELEGRAM_API_BASE + "sendMessage"
    payload = {"chat_id": config.telegram['chat_id'], "text": message}

    response = requests.post(requesturl, data=payload)
    print(response.text)
    return


def send_photo(photo_path, caption):
    print("Sending photo")
    files = {"photo": open(photo_path, "rb")}
    payload = {"chat_id": config.telegram['chat_id'], "caption": caption}
    response_raw = requests.post(TELEGRAM_API_BASE + "sendPhoto", files=files, data=payload)
    response = json.loads(response_raw.text)
    if not response.get("ok"):
        raise Exception("Telegram-Error: " + str(response.get("error_code")) + " - " + response.get("description"))
    print("Send successful")


def save_picture(url, path, cj):
    print("Saving picture "+url)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    r = opener.open(url)
    output = open(path, "wb")
    output.write(r.read())
    output.close()


if __name__ == '__main__':
    main()
