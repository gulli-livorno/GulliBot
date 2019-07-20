#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from telegram import ParseMode, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)

from api import config_dict, controllo_propietari, invia_messaggio
from const import CHAT_INSERT, COMANDI_TG, MAX_TIMEOUT

logger = logging.getLogger(__name__)

GETCHAT = 0


class risposta_asincrona:
    def __init__(self, chat_id, message_id):
        self.chat_id = chat_id
        self.message_id = message_id

    def chats(self, chat_list):
        keyboard = ReplyKeyboardMarkup(
            [[str(chat[0])] for chat in chat_list],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        invia_messaggio(
            chat_ids=[self.chat_id],
            text='Lista chats',
            reply_to_message_id=self.message_id,
            reply_markup=keyboard
        )


class handlers:
    def __init__(self, db_queue):
        self.db_queue = db_queue

    def db_inserisci_chat(self, chat_id, tipo):
        self.db_queue.put((None, CHAT_INSERT, (chat_id, tipo)))

    def help(self, update, context):
        update.message.reply_text(COMANDI_TG)
        chat = update.message.chat
        self.db_inserisci_chat(chat.id, chat.type)

    def chats(self, update, context):
        if controllo_propietari(update.message.chat.id):
            ra = risposta_asincrona(
                update.message.chat.id, update.message.message_id
            )
            update.message.reply_text('Ricerca chats in corso...')
            self.db_queue.put((ra.chats, 'SELECT `tg_id` FROM `chat`', None))
            return GETCHAT
        else:
            return ConversationHandler.END

    def getchat(self, update, context):
        chat = context.bot.get_chat(update.message.text)
        update.message.reply_text(
            'ID: *{}*\nTipo: *{}*\nTitolo: *{}*\n'
            'Username: *{}*\nNome: *{}*\nCognome: *{}*'
            .format(chat.id, chat.type, chat.title,
                    chat.username, chat.first_name, chat.last_name),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    def annulla_chats(self, update, context):
        update.message.reply_text(
            'Comando annullato!',
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    def annulla(self, update, context):
        update.message.reply_text('Nessun comando in corso!')
        return ConversationHandler.END

    def errore(self, update, context):
        logger.error(
            'Errore telegram: {}\n dall update {}'
            .format(context.error, update)
        )


def ricezione_messaggi(stop_event, stop_queue, db_queue):
    updater = Updater(config_dict()['telegram']['token'], use_context=True)
    dp = updater.dispatcher
    h = handlers(db_queue)
    conv_chats = ConversationHandler(
        entry_points=[CommandHandler('chats', h.chats)],
        states={
            GETCHAT: [MessageHandler(Filters.regex(r'^\-?\d+$'), h.getchat)]
        },
        fallbacks=[CommandHandler(['annulla', 'cancel'], h.annulla_chats)]
    )
    dp.add_handler(conv_chats)
    dp.add_handler(CommandHandler(['start', 'aiuto', 'help'], h.help))
    dp.add_handler(CommandHandler(['annulla', 'cancel'], h.annulla))
    dp.add_error_handler(h.errore)
    updater.start_polling(timeout=MAX_TIMEOUT)
    stop_event.wait()
    updater.stop()
