import logging

from telegram.ext import CommandHandler, Updater

from api import config_dict
from const import COMANDI_TG


def help(bot, update):
    update.message.reply_text(COMANDI_TG)


def errore(bot, update, error):
    logging.error(
        'Errore telegram: {}\n dall update {}'.format(error, update)
    )


def ricezione_messaggi(stop_event, stop_queue, db_queue):
    updater = Updater(config_dict()['telegram']['token'])
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', help))
    dp.add_handler(CommandHandler('aiuto', help))
    dp.add_handler(CommandHandler('help', help))
    dp.add_error_handler(errore)
    updater.start_polling()
    stop_event.wait()
    updater.stop()
