#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from time import sleep

import requests

from const import (FILE_VERSIONE, GITHUB_HEADER, GITHUB_LATEST_RELEASE,
                   INTERVALLO_CONTROLLI, VERSIONE)


class github_latest:
    def __init__(self):
        r = requests.get(GITHUB_LATEST_RELEASE, headers=GITHUB_HEADER)
        self.sc = r.status_code
        self.ok = True if self.sc == 200 else False
        self.rj = r.json() if self.ok else {}


def _aggiorna_bot(url) -> bool:
    import tarfile
    from tempfile import NamedTemporaryFile

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


def _installata_nuova_versione(versione_precedente):
    logging.info(
        'Nuova versione installata: {} > {}'
        .format(VERSIONE, versione_precedente)
    )


def _check_nuova_versione():
    with open(FILE_VERSIONE, mode='w+') as f:
        versione_su_file = f.read()
        if versione_su_file and VERSIONE > versione_su_file:
            _installata_nuova_versione(versione_su_file)
        f.write(VERSIONE)


def verifica_aggiornamenti(stop_event, stop_queue, db_queue):
    logging.debug('{} avviato'.format(__name__))
    loop = True
    while loop:
        gl = github_latest()
        if gl.ok:
            versione_github = gl.rj['tag_name']
            if VERSIONE < versione_github:
                logging.info(
                    'Download nuova versione: {}'.format(versione_github)
                )
                if _aggiorna_bot(gl.rj['tarball_url']):
                    stop_queue.put(100)
        else:
            logging.warning(
                '{} - Errore risposta github: {}'.format(__name__, gl.sc)
            )
        for i in range(0, INTERVALLO_CONTROLLI):
            if stop_event.is_set():
                loop = False
            else:
                sleep(1)
    logging.debug('{} fermato'.format(__name__))
