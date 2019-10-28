#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from time import sleep

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from api import notifica_tutti
from const import (CONTROLLO_AGGIORNAMENTI_BOT, FILE_VERSIONE, GITHUB_HEADER,
                   GITHUB_LATEST_RELEASE, STORICO_VERSIONI_INSERT, VERSIONE)

logger = logging.getLogger(__name__)


class github_latest:
    def __init__(self):
        r = requests.get(GITHUB_LATEST_RELEASE, headers=GITHUB_HEADER)
        self.sc = r.status_code
        self.ok = True if self.sc == 200 else False
        self.rj = r.json() if self.ok else {}


def _aggiorna_bot(url) -> bool:
    import tarfile
    from tempfile import NamedTemporaryFile

    logger.debug("Download di {}".format(url))
    r = requests.get(url)
    if r.status_code != 200:
        logger.warning('Errore download: {}'.format(url))
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


def _check_nuova_versione(db_queue):
    with open(FILE_VERSIONE, mode='w+') as f:
        versione_su_file = f.read()
        if versione_su_file and VERSIONE > versione_su_file:
            logger.info(
                'Nuova versione installata: {} > {}'
                .format(VERSIONE, versione_su_file)
            )
            rm = InlineKeyboardMarkup.from_button(InlineKeyboardButton(
                text='GitHub',
                url='https://github.com/gulli-livorno/GulliBot/releases/latest'
            ))
            notifica_tutti(
                db_queue=db_queue,
                text='Nuova versione installata: *{}*'.format(VERSIONE),
                reply_markup=rm
            )
            db_queue.put((None, STORICO_VERSIONI_INSERT, (VERSIONE)))
        f.write(VERSIONE)


def verifica_aggiornamenti(stop_event, stop_queue, db_queue):
    logger.debug('{} avviato'.format(__name__))
    _check_nuova_versione(db_queue)
    loop = True
    while loop:
        gl = github_latest()
        if gl.ok:
            versione_github = gl.rj['tag_name']
            if VERSIONE < versione_github:
                logger.info(
                    'Download nuova versione: {}'.format(versione_github)
                )
                if _aggiorna_bot(gl.rj['tarball_url']):
                    stop_queue.put(100)
        else:
            logger.warning(
                '{} - Errore risposta github: {}'.format(__name__, gl.sc)
            )
        for i in range(0, CONTROLLO_AGGIORNAMENTI_BOT):
            if stop_event.is_set():
                loop = False
            else:
                sleep(1)
    logger.debug('{} fermato'.format(__name__))
