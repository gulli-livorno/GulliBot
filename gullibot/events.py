#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import timedelta
from time import sleep

from dateutil.parser import parse as date_parse
from googleapiclient.discovery import build

from api import config_dict, evento_msg, notifica_tutti, time_now_iso
from const import CONTROLLO_NUOVI_EVENTI

CALENDAR_EVENTS = build(
    'calendar', 'v3',
    developerKey=config_dict()['google']['key'], cache_discovery=False
).events()


def lista_eventi(eventi: dict) -> list:
    e_list = []
    for item in eventi['items']:
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
    events_json = CALENDAR_EVENTS.list(
        calendarId=config_dict()['google']['calendar_id'],
        timeMin=time_now_iso(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return lista_eventi(events_json)


def verifica_nuovi_eventi(stop_event, stop_queue, db_queue):
    sync_token = None
    loop = True
    while loop:
        events_json = CALENDAR_EVENTS.list(
            calendarId=config_dict()['google']['calendar_id'],
            syncToken=sync_token,
            singleEvents=True
        ).execute()
        if sync_token is not None:
            for e in lista_eventi(events_json):
                msg = 'Nuovo evento!\n{}'.format(evento_msg(e))
                notifica_tutti(db_queue=db_queue, text=msg)
        sync_token = events_json['nextSyncToken']
        for i in range(0, CONTROLLO_NUOVI_EVENTI):
            if stop_event.is_set():
                loop = False
            else:
                sleep(1)
