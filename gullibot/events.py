#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import timedelta
from time import sleep
from typing import Tuple

from dateutil.parser import parse as date_parse
from googleapiclient.discovery import build

from api import config_dict, evento_msg, notifica_tutti, time_now_iso
from const import CONTROLLO_NUOVI_EVENTI


def get_events(**kwargs) -> Tuple[list, str]:
    e_list = []
    page_token = None
    sync_token = None
    service = build(
        'calendar', 'v3',
        developerKey=config_dict()['google']['key'], cache_discovery=False
    )
    while True:
        event_blob = service.events().list(
            calendarId=config_dict()['google']['calendar_id'],
            pageToken=page_token,
            singleEvents=True,
            **kwargs
        ).execute()
        e_list.extend(event_blob['items'])
        page_token = event_blob.get('nextPageToken')
        if not page_token:
            sync_token = event_blob.get('nextSyncToken')
            break
    return e_list, sync_token


def lista_eventi(eventi: list) -> list:
    e_list = []
    for item in eventi:
        if item['status'] == 'confirmed':
            start_time = None
            start_date = item['start'].get('date')
            if start_date is None:
                dt = date_parse(item['start']['dateTime'])
                start_time = dt.time().isoformat(timespec='minutes')
                start_date = dt.date().strftime('%d/%m')
            else:
                start_date = date_parse(start_date).date().strftime('%d/%m')

            end_time = None
            end_date = item['end'].get('date')
            if end_date is None:
                dt = date_parse(item['end']['dateTime'])
                end_time = dt.time().isoformat(timespec='minutes')
                end_date = dt.date().strftime('%d/%m')
            else:
                dt = date_parse(end_date).date()
                end_date = (dt - timedelta(days=1)).strftime('%d/%m')

            evento = {
                'nome': item.get('summary'),
                'descrizione': item.get('description'),
                'inizio_data': start_date,
                'inizio_ora': start_time,
                'fine_data': end_date,
                'fine_ora': end_time
            }
            e_list.append(evento)
    return e_list


def eventi_futuri() -> list:
    e_list, sync_token = get_events(
        timeMin=time_now_iso(),
        orderBy='startTime'
    )
    return lista_eventi(e_list)


def verifica_nuovi_eventi(stop_event, stop_queue, db_queue):
    primo_giro = True
    sync_token = None
    loop = True
    while loop:
        e_list, sync_token = get_events(syncToken=sync_token)
        if not primo_giro:
            for e in lista_eventi(e_list):
                msg = '_Nuovo evento!_\n{}'.format(evento_msg(e))
                notifica_tutti(db_queue=db_queue, text=msg)
        primo_giro = False
        for i in range(0, CONTROLLO_NUOVI_EVENTI):
            if stop_event.is_set():
                loop = False
            else:
                sleep(1)
