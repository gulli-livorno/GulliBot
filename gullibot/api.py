#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)


def config_dict() -> dict:
    import json
    from const import CONFIG_FILE

    config = {}
    with open(CONFIG_FILE, mode='r') as f:
        config = json.load(f)
    return config


def controllo_propietari(chat_id: int) -> bool:
    if chat_id in config_dict()['telegram']['propietari_bot']:
        return True
    else:
        msg = (
            'ATTENZIONE: *{}* ha provato un comando riservato ai propietari'
            .format(chat_id)
        )
        logger.warning(msg)
        notifica_propietari(text=msg)
        invia_messaggio(
            chat_ids=[chat_id],
            text='Non sei il propietario del bot!'
        )
        return False


def invia_messaggio(chat_ids: list, text: str, **kwargs) -> bool:
    from telegram import Bot, ParseMode, TelegramError

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
        logger.error('Errore telegram: {}\n durante invio semplice'.format(e))
        return False


def notifica_propietari(text: str, **kwargs) -> bool:
    return invia_messaggio(
        chat_ids=config_dict()['telegram']['propietari_bot'],
        text=text,
        **kwargs
    )


def notifica_tutti(text: str, **kwargs) -> bool:
    pass
