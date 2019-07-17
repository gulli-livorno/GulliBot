#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from telegram.ext import CommandHandler, Updater

from api import config_dict
from const import COMANDI_TG, MAX_TIMEOUT

logger = logging.getLogger(__name__)


def help(update, context):
    update.message.reply_text(COMANDI_TG)


def errore(update, context):
    logger.error(
        'Errore telegram: {}\n dall update {}'.format(context.error, update)
    )


def ricezione_messaggi(stop_event, stop_queue, db_queue):
    updater = Updater(config_dict()['telegram']['token'], use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', help))
    dp.add_handler(CommandHandler('aiuto', help))
    dp.add_handler(CommandHandler('help', help))
    dp.add_error_handler(errore)
    updater.start_polling(timeout=MAX_TIMEOUT)
    stop_event.wait()
    updater.stop()
