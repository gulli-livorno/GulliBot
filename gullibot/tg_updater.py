from api import config_dict
from telegram.ext import Updater

def errore(update, context):
    logger.error(
        'Errore telegram: {}\n dall update {}'.format(context.error, update)
    )

def ricezione_messaggi(stop_event, stop_queue, db_queue):
    updater = Updater(config_dict()['telegram']['token'])
    dp = updater.dispatcher
    dp.add_error_handler(errore)
    updater.start_polling(timeout=60)
    stop_event.wait()
    updater.stop()
