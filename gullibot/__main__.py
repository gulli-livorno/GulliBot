#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import sys
from multiprocessing import Event, Process, Queue
from signal import SIGABRT, SIGINT, SIGTERM, signal
from time import sleep

from const import DESC_STOP, FILE_TOKENS

TOKENS_MODEL = {
    'telegram': ''
}


def main() -> int:
    logging.debug('Main avviato')
    stop_event = Event()
    stop_queue = Queue()
    db_queue = Queue()
    args_pack = (stop_event, stop_queue, db_queue)

    def signal_stop(signum, frame):
        stop_queue.put(99)
    signal(SIGINT, signal_stop)
    signal(SIGTERM, signal_stop)
    signal(SIGABRT, signal_stop)

    from db import connessione_db
    Process(target=connessione_db, args=args_pack).start()

    if '--auto-update' in sys.argv:
        from auto_update import verifica_aggiornamenti
        Process(target=verifica_aggiornamenti, args=args_pack).start()

    causa_stop = stop_queue.get(block=True)
    if causa_stop:
        stop_event.set()
    logging.debug('Main fermato: {}'.format(DESC_STOP[causa_stop]))
    if causa_stop == 100:
        sleep(10)
        os.execv(__file__, sys.argv)
    return causa_stop


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s (%(threadName)s) "
        "[%(name)s] %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
        # filename='log'
    )

    if not os.path.isfile(FILE_TOKENS):
        import json

        with open(FILE_TOKENS, mode='w') as f:
            json.dump(TOKENS_MODEL, f, indent=4)
        logging.info('Completa il file {}'.format(FILE_TOKENS))
        sys.exit(1)

    sys.exit(main())
