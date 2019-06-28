#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import tarfile
from tempfile import NamedTemporaryFile
from time import sleep

import requests

from const import (GITHUB_HEADER, GITHUB_LATEST_RELEASE, INTERVALLO_CONTROLLI,
                   VERSIONE)


class github_latest:
    def __init__(self):
        r = requests.get(GITHUB_LATEST_RELEASE, headers=GITHUB_HEADER)
        self.sc = r.status_code
        self.ok = True if self.sc == 200 else False
        self.rj = r.json() if self.ok else {}


def _aggiorna_bot(url) -> bool:
    logging.debug("Download di {}".format(url))
    r = requests.get(url)
    if r.status_code != 200:
        logging.error('Errore download: {}'.format(url))
        return False
    with NamedTemporaryFile() as f:
        f.write(r.content)
        f.seek(0)
        with tarfile.open(f.name) as tar:
            dl_dir = os.path.abspath(os.path.dirname(__file__))
            tar.extractall(path=dl_dir)
            file_dir = os.path.join(dl_dir, tar.getmembers()[0].name)
            for dir_obj in os.listdir(file_dir):
                os.rename(
                    os.path.join(file_dir, dir_obj),
                    os.path.join(dl_dir, dir_obj)
                )
            os.rmdir(file_dir)
    return True


def controllo_versione_bot(stop_event, stop_queue):
    logging.debug('{} avviato'.format(__name__))
    while not stop_event.is_set():
        gl = github_latest()
        if gl.ok:
            versione_github = gl.rj['tag_name']
            if VERSIONE < versione_github:
                logging.debug(
                    'Download nuova versione: {}'.format(versione_github)
                )
                if _aggiorna_bot(gl.rj['tarball_url']):
                    stop_queue.put(100)
        else:
            logging.warning(
                '{} - Errore risposta github: {}'.format(__name__, gl.sc)
            )
        sleep(INTERVALLO_CONTROLLI)
    logging.debug('{} fermato'.format(__name__))
