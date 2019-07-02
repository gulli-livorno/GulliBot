#!/usr/bin/env python
# -*- coding: utf-8 -*-

CHAT_SCHEMA = '''
    CREATE TABLE IF NOT EXISTS `chat` (
        `tg_id`     INTEGER NOT NULL,
        `tipo`      TEXT NOT NULL,
        `tempo`     DATETIME NOT NULL DEFAULT (DATETIME('now','localtime')),
        `notifiche` TEXT NOT NULL DEFAULT 'si',
        PRIMARY KEY(tg_id)
    ) WITHOUT ROWID;
'''

DESC_STOP = {
    99: 'Interruzione tramite signal',
    100: 'Aggiornamento bot'
}

FILE_SQLITE = 'db.sqlite'

FILE_TOKENS = 'tokens.json'

FILE_VERSIONE = 'ultima_versione'

GITHUB_HEADER = {'Accept': 'application/vnd.github.v3+json'}

GITHUB_LATEST_RELEASE = 'https://api.github.com/repos/' \
    'gulli-livorno/GulliBot/releases/latest'

INTERVALLO_CONTROLLI = 30

VERSIONE = 'v4.0-beta0'
