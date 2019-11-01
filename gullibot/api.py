#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import re
from datetime import datetime, timezone
from html import unescape as html_unescape
from multiprocessing import Queue

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


class notifica_asincrona:
    def __init__(self, text: str, **kwargs):
        self.text = text
        self.kwargs = kwargs

    def tutti(self, ids: list):
        ids = [x[0] for x in ids]
        invia_messaggio(chat_ids=ids, text=self.text, **self.kwargs)


def notifica_tutti(db_queue: Queue, text: str, **kwargs) -> bool:
    db_queue.put((
        notifica_asincrona(text=text, **kwargs).tutti,
        'SELECT `tg_id` FROM `chat` WHERE `notifiche`=\'si\'',
        None
    ))


def evento_msg(e: dict) -> str:
    msg = '*{}*\n'.format(e['nome'])
    if e['descrizione']:
        msg += '_{}_\n'.format(e['descrizione'])
    if e['inizio_data'] == e['fine_data']:
        msg += 'Il *{}*\n'.format(e['inizio_data'])
        if e['inizio_ora'] and e['fine_ora']:
            msg += ('Ore *{}* - *{}*'
                    .format(e['inizio_ora'], e['fine_ora']))
    else:
        if e['inizio_ora'] and e['fine_ora']:
            msg += ('Dal *{}* ore *{}*\nAl *{}* ore *{}*\n'
                    .format(e['inizio_data'], e['inizio_ora'],
                            e['fine_data'], e['fine_ora']))
        else:
            msg += ('Dal *{}*\nAl *{}*\n'
                    .format(e['inizio_data'], e['fine_data']))
    return msg


def time_now() -> datetime:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0)


def time_now_iso() -> str:
    return time_now().isoformat()


def clean_html(html: str):
    html = re.sub('<.*$', '', html)
    return html_unescape(html)
