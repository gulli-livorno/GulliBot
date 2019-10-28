#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)

from api import config_dict, controllo_propietari, evento_msg, notifica_tutti
from const import CHAT_INSERT, COMANDI_TG, MAX_TIMEOUT, COMANDI_TG_OWNER
from events import eventi_futuri
from feed import scarica_feed

logger = logging.getLogger(__name__)

ANNULLA = '/annulla comando'


class risposta_asincrona:
    def __init__(self, message):
        self.message = message

    def chats(self, chat_list):
        self.message.reply_text(
            'Seleziona una chat. {}'.format(ANNULLA),
            reply_markup=ReplyKeyboardMarkup.from_column(
                [str(chat[0]) for chat in chat_list],
                resize_keyboard=True, one_time_keyboard=True
            ),
            quote=False
        )

    def notifiche(self, notifiche_attive):
        na = (str(notifiche_attive[0][0]) == 'si')
        stato_notifiche = 'sono attive' if na else 'non sono attive'
        self.message.reply_text(
            'Le notifiche *{}*. {}'.format(stato_notifiche, ANNULLA),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup.from_button(
                'Disattiva' if na else 'Attiva',
                resize_keyboard=True, one_time_keyboard=True
            ),
            quote=False
        )


class handlers:
    def __init__(self, db_queue, stop_queue):
        self.db_queue = db_queue
        self.stop_queue = stop_queue

    def db_inserisci_chat(self, chat_id, tipo):
        self.db_queue.put((None, CHAT_INSERT, (chat_id, tipo)))

    def help(self, update, context):
        update.message.reply_text(COMANDI_TG, quote=False)
        chat = update.message.chat
        self.db_inserisci_chat(chat.id, chat.type)

    def help_owner(self, update, context):
        if controllo_propietari(update.message):
            update.message.reply_text(COMANDI_TG_OWNER, quote=False)

    # Conversazione del comando chat - OWNER
    def chats(self, update, context):
        if controllo_propietari(update.message):
            update.message.reply_text('Ricerca chats in corso...', quote=False)
            self.db_queue.put((
                risposta_asincrona(update.message).chats,
                'SELECT `tg_id`, `tipo` FROM `chat`',
                None
            ))
            return 0
        else:
            return ConversationHandler.END

    def risposta_chats(self, update, context):
        chat = context.bot.get_chat(update.message.text)
        update.message.reply_text(
            'ID: *{}*\nTipo: *{}*\nTitolo: *{}*\n'
            'Username: *{}*\nNome: *{}*\nCognome: *{}*'
            .format(chat.id, chat.type, chat.title,
                    chat.username, chat.first_name, chat.last_name),
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove(),
            quote=False
        )
        return ConversationHandler.END

    # Conversazione del comando notifiche - ADMIN
    def notifiche(self, update, context):
        chat = update.message.chat
        chat_private = (chat.type == 'private')
        member_admin = context.bot.get_chat_member(
            chat.id, update.message.from_user.id
        ).status in ['creator', 'administrator']

        if chat_private or member_admin:
            self.db_inserisci_chat(chat.id, chat.type)
            update.message.reply_text('Ricerca preferenze in corso...',
                                      quote=False)
            self.db_queue.put((
                risposta_asincrona(update.message).notifiche,
                'SELECT `notifiche` FROM `chat` WHERE `tg_id`=?',
                (chat.id,)
            ))
            return 0
        else:
            update.message.reply_text('Non sei un amministratore!',
                                      quote=False)
            return ConversationHandler.END

    def risposta_notifiche(self, update, context):
        notifiche_attive = 'si' if update.message.text == 'Attiva' else 'no'
        self.db_queue.put((
            None,
            'UPDATE `chat` SET `notifiche`=? WHERE `tg_id`=?',
            (notifiche_attive, update.message.chat.id)
        ))
        update.message.reply_text(
            'Preferenza modificata',
            reply_markup=ReplyKeyboardRemove(),
            quote=False
        )
        return ConversationHandler.END

    # Comando articoli
    def articoli(self, update, context):
        articoli = scarica_feed()
        if not articoli:
            update.message.reply_text('*Nessun articolo presente*',
                                      parse_mode='Markdown', quote=False)
        for a in articoli:
            msg = '*{}*\n{}'.format(a['titolo'], a['descrizione'])
            rm = None
            if 'link' in a:
                rm = InlineKeyboardMarkup.from_button(InlineKeyboardButton(
                    text='Vai all\'articolo', url=a['link']
                ))
            update.message.reply_text(msg, parse_mode='Markdown',
                                      reply_markup=rm, quote=False)

    # Comando eventi
    def eventi(self, update, context):
        eventi = eventi_futuri()
        if not eventi:
            update.message.reply_text('*Nessun evento in programma*',
                                      parse_mode='Markdown', quote=False)
        for e in eventi:
            update.message.reply_text(evento_msg(e),
                                      parse_mode='Markdown', quote=False)

    # Comando broadcast - OWNER
    def broadcast(self, update, context):
        if controllo_propietari(update.message):
            if update.message.reply_to_message:
                msg = update.message.reply_to_message.text
                notifica_tutti(db_queue=self.db_queue, text=msg)
            else:
                update.message.reply_text('Metti un messaggio in risposta',
                                          quote=False)

    # Comando reboot - OWNER
    def reboot(self, update, context):
        if controllo_propietari(update.message):
            update.message.reply_text('Riavvio in corso...', quote=False)
            self.stop_queue.put(101)

    def annulla_conv(self, update, context):
        update.message.reply_text(
            'Comando annullato!',
            reply_markup=ReplyKeyboardRemove(),
            quote=False
        )
        return ConversationHandler.END

    def annulla(self, update, context):
        update.message.reply_text('Nessun comando in corso!', quote=False)
        return ConversationHandler.END

    def errore(self, update, context):
        logger.error(
            'Errore telegram: {}\n dall update {}'
            .format(context.error, update)
        )


def ricezione_messaggi(stop_event, stop_queue, db_queue):
    updater = Updater(config_dict()['telegram']['token'], use_context=True)
    dp = updater.dispatcher
    h = handlers(db_queue, stop_queue)
    annulla_conv_cmd = CommandHandler(['annulla', 'cancel'], h.annulla_conv)
    conv_chats = ConversationHandler(
        entry_points=[CommandHandler('chats', h.chats)],
        states={
            0: [MessageHandler(Filters.regex(r'^\-?\d+$'), h.risposta_chats)]
        },
        fallbacks=[annulla_conv_cmd]
    )
    conv_notifiche = ConversationHandler(
        entry_points=[CommandHandler(['notifiche', 'settings'], h.notifiche)],
        states={
            0: [MessageHandler(
                Filters.regex(r'^(Attiva|Disattiva)$'), h.risposta_notifiche
            )]
        },
        fallbacks=[annulla_conv_cmd]
    )
    dp.add_handler(conv_chats)
    dp.add_handler(conv_notifiche)
    dp.add_handler(CommandHandler(['start', 'aiuto', 'help'], h.help))
    dp.add_handler(CommandHandler(['owner', 'sudo'], h.help_owner))
    dp.add_handler(CommandHandler(['articoli', 'feed'], h.articoli))
    dp.add_handler(CommandHandler(['eventi', 'events'], h.eventi))
    dp.add_handler(CommandHandler(['bc'], h.broadcast))
    dp.add_handler(CommandHandler(['reboot'], h.reboot))
    dp.add_handler(CommandHandler(['annulla', 'cancel'], h.annulla))
    dp.add_error_handler(h.errore)
    updater.start_polling(timeout=MAX_TIMEOUT)
    stop_event.wait()
    updater.stop()
