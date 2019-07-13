#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging


def config_dict() -> dict:
    import json
    from const import CONFIG_FILE

    config = {}
    with open(CONFIG_FILE, mode='r') as f:
        config = json.load(f)
    return config


def invia_messaggio(chat_ids: list, text: str, **kwargs) -> bool:
    from telegram import Bot, ParseMode
    from telegram.error import TelegramError

    try:
        bot = Bot(config_dict()['telegram']['token'])
        for id in chat_ids:
            bot.send_message(
                chat_id=id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                **kwargs
            )
        return True
    except TelegramError as e:
        logging.error('Errore telegram: {}\n durante invio semplice'.format(e))
        return False


def notifica_propietari(text: str, **kwargs) -> bool:
    return invia_messaggio(
        chat_ids=config_dict()['telegram']['propietari_bot'],
        text=text,
        **kwargs
    )
