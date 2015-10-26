# MonstercatConnectNotifier
[![Build Status](https://travis-ci.org/z3ntu/MonstercatConnectNotifier.svg)](https://travis-ci.org/z3ntu/MonstercatConnectNotifier)
## Requirements
- Python 3 or newer
- A Monstercat Connect account ($9.99/Month, get 25% discount with my [referral link](https://connect.monstercat.com/#referral/NJvESmuF46kl
))
- A Telegram account

## Setup
- Copy `config.DEFAULT.py` to `config.py`

#### Create your Telegram bot
  - Write `/newbot` to [@BotFather](http://telegram.me/botfather) on Telegram and follow the instructions
  - Copy the token you get at the end into `bot_token` in `config.py`

#### Create your Telegram channel
This depends on the platform you are doing this on (these instructions are for Telegram desktop)
- Click the "create" icon in the search field
- Choose `New channel` and give it a name
- Add your bot (use the @username) as an administrator to the channel
- Copy the channel username into `chat_id` in `config.py` (that it looks like `chat_id="@ConnectNotifier")

#### General
- Enter your Monstercat Connect credentials into `config.py` into their respective places
- Start `notifier.py`
