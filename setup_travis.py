#!/usr/bin/python3

import os


def main():
    template_file = open("config.DEFAULT.py", "r")
    config = open("config.py", "w")

    template = template_file.read()
    template = template.replace("email=\"\"", "email=\""+os.environ['EMAIL']+"\"")
    template = template.replace("password=\"\"", "password=\""+os.environ['PASSWORD']+"\"")
    template = template.replace("bot_token=\"\"", "bot_token=\""+os.environ['BOT_TOKEN']+"\"")
    template = template.replace("chat_id=\"\"", "chat_id=\""+os.environ['CHAT_ID']+"\"")

    config.write(template)

if __name__ == '__main__':
    main()
