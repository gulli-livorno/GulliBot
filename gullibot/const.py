#!/usr/bin/env python
# -*- coding: utf-8 -*-

ATOM_FEED = 'https://linux.livorno.it/sito/feed/atom/'

CHAT_INSERT = 'INSERT OR IGNORE INTO `chat` (`tg_id`, `tipo`) VALUES(?, ?);'

CHAT_SCHEMA = '''
    CREATE TABLE IF NOT EXISTS `chat` (
        `tg_id`     INTEGER NOT NULL,
        `tipo`      TEXT NOT NULL,
        `tempo`     DATETIME NOT NULL DEFAULT (DATETIME('now','localtime')),
        `notifiche` TEXT NOT NULL DEFAULT 'si',
        PRIMARY KEY(tg_id)
    ) WITHOUT ROWID;
'''

COMANDI_TG = '''
Comandi disponibili:
/start - Lista comandi disponibili
/aiuto - Lista comandi disponibili
/help - Lista comandi disponibili
/info - Info bot
/articoli - Mostra gli utlimi articoli
/eventi - Prossimi eventi
/annulla - Annulla comando attivo
/cancel - Annulla comando attivo
/notifiche - Dis/attiva notifiche
/settings - Dis/attiva notifiche
'''

COMANDI_TG_OWNER = '''
/bc - Inoltra a chi ha attive le notifiche, il messaggio a cui rispondi
/chats - Informazioni sulle chat che interagiscono con il bot
/reboot - Riavvia il bot
'''

CONFIG_FILE = 'config.json'

CONFIG_MODEL = {
    'telegram': {
        'token': '',
        'propietari_bot': []
    },
    'google': {
        'key': '',
        'calendar_id': 'gulligle@gmail.com'
    }
}

CONTROLLO_AGGIORNAMENTI_BOT = 60

CONTROLLO_NUOVI_EVENTI = 60

DESC_STOP = {
    99: 'Interruzione tramite signal',
    100: 'Aggiornamento bot',
    101: 'Riavvio manuale bot'
}

FILE_SQLITE = 'db.sqlite'

FILE_VERSIONE = 'ultima_versione'

GITHUB_HEADER = {'Accept': 'application/vnd.github.v3+json'}

GITHUB_LATEST_RELEASE = 'https://api.github.com/repos/' \
    'gulli-livorno/GulliBot/releases/latest'

MAX_TIMEOUT = 20

STORICO_VERSIONI_INSERT = 'INSERT OR IGNORE INTO `storico_versioni` ' \
    '(`versione`) VALUES(?);'

STORICO_VERSIONI_SCHEMA = '''
    CREATE TABLE IF NOT EXISTS `storico_versioni` (
        `versione` TEXT NOT NULL,
        `tempo`    DATETIME NOT NULL DEFAULT (DATETIME('now','localtime')),
        PRIMARY KEY(versione)
    ) WITHOUT ROWID;
'''

VERSIONE = 'v4.0-beta1'
