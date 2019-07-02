#!/usr/bin/env python
# -*- coding: utf-8 -*-

DESC_STOP = {
    99: 'Interruzione tramite signal',
    100: 'Aggiornamento bot'
}

FILE_VERSIONE = 'ultima_versione'

FILE_TOKENS = 'tokens.json'

GITHUB_HEADER = {'Accept': 'application/vnd.github.v3+json'}

GITHUB_LATEST_RELEASE = 'https://api.github.com/repos/' \
    'gulli-livorno/GulliBot/releases/latest'

INTERVALLO_CONTROLLI = 30

VERSIONE = 'v1.0-beta0'
