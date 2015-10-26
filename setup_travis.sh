#!/bin/bash

CONTENT="
connect = dict(
    email=\"$EMAIL\",
    password=\"$PASSWORD\"
)

telegram = dict(
    bot_token=\"$BOT_TOKEN\",
    chat_id=\"$CHAT_ID\"
)
"

echo $CONTENT > config.py