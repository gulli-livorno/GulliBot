#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sqlite3
from threading import Thread

from const import (CHAT_SCHEMA, FILE_SQLITE, MAX_TIMEOUT,
                   STORICO_VERSIONI_SCHEMA)

logger = logging.getLogger(__name__)


def _inizializza_db(db_queue):
    db_queue.put((None, CHAT_SCHEMA, None))
    db_queue.put((None, STORICO_VERSIONI_SCHEMA, None))


def connessione_db(stop_event, stop_queue, db_queue):
    from queue import Empty
    logger.debug('{} avviato'.format(__name__))
    conn = sqlite3.connect(FILE_SQLITE)
    curs = conn.cursor()
    _inizializza_db(db_queue)
    loop = True
    while loop:
        try:
            func, sql, param = db_queue.get(block=True, timeout=MAX_TIMEOUT)
            curs.execute(sql, param) if param else curs.execute(sql)
            if func is None:
                conn.commit()
            else:
                Thread(
                    target=func,
                    args=(curs.fetchall(),),
                    daemon=True
                ).start()
        except Empty:
            if stop_event.is_set():
                loop = False
    conn.close()
    logger.debug('{} fermato'.format(__name__))
