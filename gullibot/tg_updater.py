#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from telegram.ext import CommandHandler, Updater

from api import config_dict
from const import CHAT_INSERT, COMANDI_TG, MAX_TIMEOUT

logger = logging.getLogger(__name__)


class handlers:
    def __init__(self, db_queue):
        self.db_queue = db_queue

    def db_inserisci_chat(self, chat_id, tipo):
        self.db_queue.put((None, CHAT_INSERT, (chat_id, tipo)))

    def help(self, update, context):
        update.message.reply_text(COMANDI_TG)
        chat = update.message.chat
        self.db_inserisci_chat(chat.id, chat.type)

    def errore(self, update, context):
        logger.error(
            'Errore telegram: {}\n dall update {}'
            .format(context.error, update)
        )


def ricezione_messaggi(stop_event, stop_queue, db_queue):
    updater = Updater(config_dict()['telegram']['token'], use_context=True)
    dp = updater.dispatcher
    h = handlers(db_queue)
    dp.add_handler(CommandHandler(['start', 'aiuto', 'help'], h.help))
    dp.add_error_handler(h.errore)
    updater.start_polling(timeout=MAX_TIMEOUT)
    stop_event.wait()
    updater.stop()
