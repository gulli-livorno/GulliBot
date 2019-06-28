#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import signal
import sys
from multiprocessing import Event, Process, Queue
from time import sleep

from const import DESC_STOP
from controllo_versioni import controllo_versione_bot


def main() -> str:
    logging.debug('Main avviato')
    stop_event = Event()
    stop_queue = Queue()
    stop_pack = (stop_event, stop_queue)

    def signal_stop(signum, frame):
        stop_queue.put(99)
    signal.signal(signal.SIGINT, signal_stop)
    signal.signal(signal.SIGTERM, signal_stop)
    signal.signal(signal.SIGABRT, signal_stop)

    if '--no-update' not in sys.argv:
        Process(target=controllo_versione_bot, args=stop_pack).start()

    causa_stop = stop_queue.get(block=True)
    if causa_stop:
        stop_event.set()
    logging.debug('Main fermato: {}'.format(DESC_STOP[causa_stop]))
    if causa_stop == 100:
        sleep(causa_stop)
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

    sys.exit(main())
