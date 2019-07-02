#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sqlite3

from const import CHAT_SCHEMA, FILE_SQLITE


def _inizializza_db(db_queue):
    db_queue.put((None, CHAT_SCHEMA, None))


def connessione_db(stop_event, stop_queue, db_queue):
    from queue import Empty
    logging.debug('{} avviato'.format(__name__))
    conn = sqlite3.connect(FILE_SQLITE)
    _inizializza_db(db_queue)
    loop = True
    while loop:
        try:
            func, sql, param = db_queue.get(block=True, timeout=5)
            conn.execute(sql, param) if param else conn.execute(sql)
            if func is None:
                conn.commit()
            else:
                func(conn.fetchall())
        except Empty:
            if stop_event.is_set():
                loop = False
    conn.close()
    logging.debug('{} fermato'.format(__name__))
