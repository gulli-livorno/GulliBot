#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import sys
from multiprocessing import Event, Process, Queue
from queue import Empty
from signal import SIGABRT, SIGINT, SIGTERM, signal
from time import sleep

from api import notifica_propietari
from const import CONFIG_FILE, CONFIG_MODEL, DESC_STOP, MAX_TIMEOUT, VERSIONE

logger = logging.getLogger(__name__)


def main() -> int:
    logger.debug('Main avviato')
    notifica_propietari(text='Bot avviato\nVersione: *{}*'.format(VERSIONE))

    stop_event = Event()
    stop_queue = Queue()
    db_queue = Queue()
    args_pack = (stop_event, stop_queue, db_queue)

    def signal_stop(signum, frame):
        stop_queue.put(99)
    signal(SIGINT, signal_stop)
    signal(SIGTERM, signal_stop)
    signal(SIGABRT, signal_stop)

    process_list = []

    from db import connessione_db
    db_process = Process(
        target=connessione_db,
        name='Connessione DB',
        args=args_pack
    )
    db_process.start()
    process_list.append(db_process)

    from tg_updater import ricezione_messaggi
    updater_process = Process(
        target=ricezione_messaggi,
        name='Ricezione messaggi telegram',
        args=args_pack
    )
    updater_process.start()
    process_list.append(updater_process)

    from events import verifica_nuovi_eventi
    events_process = Process(
        target=verifica_nuovi_eventi,
        name='Verifica nuovi eventi',
        args=args_pack
    )
    events_process.start()
    process_list.append(events_process)

    if '--auto-update' in sys.argv:
        from auto_update import verifica_aggiornamenti
        update_process = Process(
            target=verifica_aggiornamenti,
            name='Verifica aggiornamenti',
            args=args_pack
        )
        update_process.start()
        process_list.append(update_process)

    loop = True
    causa_stop = ''
    while loop:
        try:
            causa_stop = stop_queue.get(block=True, timeout=MAX_TIMEOUT)
            loop = False
        except Empty:
            for proc in process_list:
                if not proc.is_alive():
                    msg = 'Il processo *{}* è morto!'.format(proc.name)
                    logger.error(msg)
                    notifica_propietari(text=msg)
                    process_list.remove(proc)
    if causa_stop:
        stop_event.set()
    logger.info('Main fermato: {}'.format(DESC_STOP[causa_stop]))
    if causa_stop in [100, 101]:
        sleep(MAX_TIMEOUT+10)
        os.execv(__file__, sys.argv)
    return causa_stop


if __name__ == "__main__":
    log_level = logging.DEBUG if '--verbose' in sys.argv else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s (%(threadName)s) "
        "[%(name)s] %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
        # filename='log'
    )
    # Silenzia API google
    logging.getLogger('googleapiclient.discovery').setLevel(logging.WARNING)

    if not os.path.isfile(CONFIG_FILE):
        import json

        with open(CONFIG_FILE, mode='w') as f:
            json.dump(CONFIG_MODEL, f, indent=4, sort_keys=True)
        logger.info('Completa il file {}'.format(CONFIG_FILE))
        sys.exit(1)

    sys.exit(main())
