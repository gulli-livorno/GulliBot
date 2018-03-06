import logging
from datiBot import telegram, google
import requests


def get(servizio, metodo='', params=None):
    url = ''
    if servizio == 'telegram':
        url = telegram['url'] + telegram['token'] + metodo
    if servizio == 'google':
        url = google['url'] + google['calId'] + metodo
        params['key'] = google['token']
    try:
        risposta = requests.get(url, params=params)
        if risposta.status_code == 200:
            return False, risposta
        else:
            logging.debug(risposta.text)
            return 'Codice risposta errato', risposta
    except requests.exceptions.ConnectionError:
        return 'Errore di connessione', None


def post(servizio, metodo='', data=None):
    url = ''
    if servizio == 'telegram':
        url = telegram['url'] + telegram['token'] + metodo
    try:
        risposta = requests.post(
            url,
            headers={'Content-Type': 'application/json'},
            json=data
        )
        if risposta.status_code == 200:
            return False, risposta
        else:
            logging.debug(risposta.text)
            return 'Codice risposta errato', risposta
    except requests.exceptions.ConnectionError:
        return 'Errore di connessione', None
