#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
/eventi - Prossimi eventi
/annulla - Annulla comando attivo
/notifiche - Dis/attiva notifiche
/settings - Dis/attiva notifiche
'''

CONFIG_FILE = 'config.json'

CONFIG_MODEL = {
    'telegram': {
        'token': '',
        'propietari_bot': []
    }
}

CONTROLLO_AGGIORNAMENTI_BOT = 30

DESC_STOP = {
    99: 'Interruzione tramite signal',
    100: 'Aggiornamento bot'
}

FILE_SQLITE = 'db.sqlite'

FILE_VERSIONE = 'ultima_versione'

GITHUB_HEADER = {'Accept': 'application/vnd.github.v3+json'}

GITHUB_LATEST_RELEASE = 'https://api.github.com/repos/' \
    'gulli-livorno/GulliBot/releases/latest'

MAX_TIMEOUT = 20

VERSIONE = 'v4.0-beta0'
