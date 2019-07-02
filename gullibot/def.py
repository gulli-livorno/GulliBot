#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging


def tokens_dict() -> dict:
    import json
    from const import FILE_TOKENS

    tokens = {}
    with open(FILE_TOKENS, mode='r') as f:
        tokens = json.load(f)
    return tokens


def invia_messaggio(chat_id, text) -> bool:
    from telegram import Bot, ParseMode
    from telegram.error import TelegramError

    try:
        bot = Bot(tokens_dict()['telegram'])
        bot.send_message(chat_id, text, parse_mode=ParseMode.MARKDOWN)
    except TelegramError as e:
        logging.error('Errore telegram: {}'.format(e))


def notifica_tutti() -> bool:
    pass
