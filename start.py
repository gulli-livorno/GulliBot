import logging
import sys
import signal
import os
import sqlite3
import threading
import partenze
import arrivi

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s@%(asctime)s@%(process)d@%(module)s@%(message)s',
    datefmt='%d/%m/%y %H:%M:%S',
    filename='log'
)

if len(sys.argv) > 1:
    for arg in sys.argv:
        if arg == '-test':
            logging.info('test OK')
        if arg == '-exit':
            sys.exit('Uscita forzata')
        if arg == '-reset-log':
            open('log', 'w').close()
        if arg == '-reset-db':
            os.remove('db.sqlite')
            logging.info('Database rimosso')
        if arg == '-crea-db':
            conn = sqlite3.connect('db.sqlite')
            conn.cursor().execute('''
                CREATE TABLE `chat` (
                    `id`            INTEGER NOT NULL,
                    `tipo`          TEXT NOT NULL,
                    `creata`        TEXT NOT NULL,
                    `notifiche`     TEXT NOT NULL DEFAULT 'si',
                    `comando`       TEXT,
                    `titolo`        TEXT,
                    `nome`          TEXT,
                    `cognome`       TEXT,
                    `username`      TEXT,
                    `accessi`       INTEGER NOT NULL DEFAULT 0,
                    `aggiornata`    TEXT,
                    PRIMARY KEY(id)
                ) WITHOUT ROWID;
            ''')
            conn.cursor().execute('''
                CREATE TABLE `inoltro` (
                    `orario`    TEXT NOT NULL,
                    `testo`     TEXT NOT NULL
                );
            ''')
            conn.commit()
            conn.close()
            logging.info('Database e tabelle creati')

# Gestione interruzione script
open('script.run', 'w').close()


def bloccaEsec(signum, frame):
    os.remove('script.run')


signal.signal(signal.SIGINT, bloccaEsec)
signal.signal(signal.SIGTERM, bloccaEsec)


class sqliteCls(object):
    def __init__(self):
        super(sqliteCls, self).__init__()
        self.dbLock = threading.Lock()
        self.dbConn = sqlite3.connect('db.sqlite', check_same_thread=False)

    def eseg(self, query, listaVar=None, recDati=None):
        recList = None
        self.dbLock.acquire(blocking=True, timeout=60)
        if listaVar:
            selez = self.dbConn.cursor().execute(query, listaVar)
        else:
            selez = self.dbConn.cursor().execute(query)
        self.dbConn.commit()
        if recDati == 'one':
            recList = selez.fetchone()
        if recDati == 'all':
            recList = selez.fetchall()
        self.dbLock.release()
        return recList

    def close(self):
        self.dbConn.close()


dbCls = sqliteCls()

arrivi.threadArrivi(name='Arrivi', db=dbCls).start()
partenze.threadPartenze(name='Partenze', db=dbCls).start()
