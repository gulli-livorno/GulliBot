#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging

from telegram import Bot, Message, TelegramError

from const import CONFIG_FILE

logger = logging.getLogger(__name__)


def config_dict() -> dict:
    config = {}
    with open(CONFIG_FILE, mode='r') as f:
        config = json.load(f)
    return config


def controllo_propietari(message: Message) -> bool:
    if message.from_user.id in config_dict()['telegram']['propietari_bot']:
        return True
    else:
        msg = (
            'ATTENZIONE: *{}* ha provato un comando riservato ai propietari.'
            ' Cercalo con /chats'.format(message.from_user.id)
        )
        logger.warning(msg)
        notifica_propietari(text=msg)
        message.reply_text('Non sei il propietario del bot!')
        return False


def invia_messaggio(chat_ids: list, text: str, **kwargs) -> bool:
    try:
        bot = Bot(config_dict()['telegram']['token'])
        for id in chat_ids:
            bot.send_message(
                chat_id=id,
                text=text,
                parse_mode='Markdown',
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
