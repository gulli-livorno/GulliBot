from datetime import datetime
from rfc3339 import rfc3339
import json
import requests
import signal
import time
import os.path
import sqlite3

# Dati bot
token = ""
apiUrl = "https://api.telegram.org/bot"
auT = apiUrl + token
timeout = 15

# Gestione interruzione script
run = True
startTime = time.time()


def handler_stop_signals(signum, frame):
    global run
    run = False

signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)

# Creazione dei database
dbFile = 'logBase.sqlite'
dbEsiste = os.path.isfile(dbFile)
connDB = sqlite3.connect(dbFile)
cursDB = connDB.cursor()
lastRicCyc = 1

if not dbEsiste:
    cursDB.executescript(
        '''
            CREATE TABLE `lastRic` (
                `id`            INTEGER NOT NULL UNIQUE,
                `rfcTime`       TEXT NOT NULL,
                `urlRic`        TEXT NOT NULL,
                `textRic`       TEXT NOT NULL
            );
            CREATE TABLE `provRichieste` (
                `chat`          INTEGER NOT NULL UNIQUE,
                `rfcTime`       TEXT NOT NULL,
                `totRic`        INTEGER NOT NULL
            );
            CREATE TABLE `errori` (
                `id`            INTEGER PRIMARY KEY AUTOINCREMENT,
                `rfcTime`       TEXT NOT NULL,
                `tipoErrore`    TEXT NOT NULL
            );
        '''
    )
    connDB.commit()


try:
    offsetFile = open('offset', 'r')
    offset = int(offsetFile.read())
    offsetFile.close()
except FileNotFoundError:
    offset = -1

urlRichiesta = apiUrl + token + '/getMe'
infoBot = requests.get(urlRichiesta)
infoBotDict = json.loads(infoBot.text)
botUsername = infoBotDict['result']['username']


def rfcTime():
    return str(rfc3339(datetime.now()))


def salvaErrore(tipoErrore):
    cursDB.execute(
        'INSERT INTO `errori` (`rfcTime`, `tipoErrore`) VALUES (?, ?);',
        (rfcTime(), str(tipoErrore))
    )
    connDB.commit()


def salvaProv(chatId, tipoRichiesta):
    cursDB.execute(
        'INSERT OR IGNORE INTO `provRichieste` VALUES (?, ?, 0);',
        (int(chatId), rfcTime())
    )
    cursDB.execute(
        'UPDATE `provRichieste` SET rfcTime=?, totRic=totRic+1 WHERE chat=?',
        (rfcTime(), int(chatId))
    )
    connDB.commit()


def nuovaRichiesta(urlRic, parRic=None, datRic=None):
    try:
        if parRic:
            risposta = requests.get(urlRic, params=parRic)
        elif datRic:
            headers = {'Content-Type': 'application/json'}
            risposta = requests.post(
                urlRic,
                headers=headers,
                data=json.dumps(datRic)
            )
        else:
            risposta = requests.get(urlRic)
    except requests.exceptions.ConnectionError:
        salvaErrore('Errore di connessione')
        time.sleep(60)
        risposta = nuovaRichiesta(urlRic, parRic=parRic, datRic=datRic)

    if risposta.status_code != 200:
        salvaErrore('Codice non corretto -> ' + str(risposta.status_code))
        time.sleep(60)
        risposta = nuovaRichiesta(urlRic, parRic=parRic, datRic=datRic)

    global lastRicCyc
    if lastRicCyc > 10:
        lastRicCyc = 1

    cursDB.execute(
        'INSERT OR REPLACE INTO `lastRic` VALUES (?, ?, ?, ?);',
        (lastRicCyc, rfcTime(), str(urlRic), str(risposta.text))
    )
    connDB.commit()
    lastRicCyc += 1

    return risposta


def sendMessage(chatId, text):
    urlRic = auT + '/sendMessage'
    parRic = {
        'chat_id': str(chatId),
        'text': str(text)
    }
    nuovaRichiesta(urlRic, parRic=parRic)


def estrNomeUser(memberDict):
    nu = memberDict['first_name']
    if 'username' in memberDict:
        nu += ' a.k.a. @' + memberDict['username']
    return nu


def verComando(testo, comando):
    amm = False
    if testo == comando:
        amm = True
    elif testo == comando + '@' + botUsername:
        amm = True
    return amm


def botOnlineText(time):
    return str('Bot *online* da _' + str(time) + ' Secondi_')


def pluraliTemp(temp, unita):
    if temp == 1:
        temp = str(temp)
        if unita == 'Minuti':
            temp = temp + ' Minuto '
        elif unita == 'Ore':
            temp = temp + ' Ora '
        elif unita == 'Giorni':
            temp = temp + ' Giorno '
        return temp
    else:
        temp = str(temp)
        temp = temp + ' ' + unita + ' '
        return temp


while True:
    if not run:
        offsetFile = open('offset', 'w')
        offsetFile.write(str(offset))
        offsetFile.close()

        cursDB.close()
        connDB.close()

        break

    urlRic = auT + '/getUpdates'
    parRic = {
        'offset': str(offset),
        'timeout': str(timeout)
    }
    rispostaDict = json.loads(nuovaRichiesta(urlRic, parRic=parRic).text)

    for result in rispostaDict['result']:
        offset = int(result['update_id'])+1

        if 'message' in result:
            chatId = str(result['message']['chat']['id'])
            salvaProv(chatId, 'message')
            if 'new_chat_member' in result['message']:
                memberDict = result['message']['new_chat_member']
                sendMessage(
                    chatId,
                    'Benvenuto/a ' + estrNomeUser(memberDict)
                )
            if 'text' in result['message']:
                text = result['message']['text']
                if verComando(text, '/stato'):
                    secUptime = str(int(time.time() - startTime))
                    urlRic = auT + '/sendMessage'
                    datRic = {
                        'chat_id': chatId,
                        'text': botOnlineText(secUptime),
                        'parse_mode': 'Markdown',
                        'reply_markup': {'inline_keyboard': [[
                                    {
                                        'text': 'Giorni',
                                        'callback_data': 'giorni,'+secUptime
                                    },
                                    {
                                        'text': 'Ore',
                                        'callback_data': 'ore,'+secUptime
                                    },
                                    {
                                        'text': 'Minuti',
                                        'callback_data': 'minuti,'+secUptime
                                    }
                                ]]}
                    }
                    nuovaRichiesta(urlRic, datRic=datRic)
                if verComando(text, '/aiuto'):
                    cmdAiutoFile = open('cmdAiuto.txt', 'r')
                    sendMessage(
                        chatId,
                        str(cmdAiutoFile.read())
                    )
                    cmdAiutoFile.close()
                if verComando(text, '/saluta'):
                    memberDict = result['message']['from']
                    sendMessage(
                        chatId,
                        'Ciao ' + estrNomeUser(memberDict)
                    )
        if 'callback_query' in result:
            callback = result['callback_query']
            chatId = str(callback['message']['chat']['id'])
            salvaProv(chatId, 'callback')
            if 'data' in callback:
                messageId = str(callback['message']['message_id'])
                messageText = str(callback['message']['text'])
                divDati = callback['data'].split(',')
                calcTime = None
                toTime = str(divDati[0])

                minuti, secondi = divmod(int(divDati[1]), 60)
                if 'minuti' == toTime:
                    calcTime = pluraliTemp(minuti, 'Minuti') \
                        + str(secondi)
                ore, minuti = divmod(minuti, 60)
                if 'ore' == toTime:
                    calcTime = pluraliTemp(ore, 'Ore') \
                        + pluraliTemp(minuti, 'Minuti') \
                        + str(secondi)
                giorni, ore = divmod(ore, 24)
                if 'giorni' == toTime:
                    calcTime = pluraliTemp(giorni, 'Giorni') \
                        + pluraliTemp(ore, 'Ore') \
                        + pluraliTemp(minuti, 'Minuti') \
                        + str(secondi)

                if calcTime:
                    editText = botOnlineText(calcTime)
                    urlRic = auT + '/editMessageText'
                    parRic = {
                        'chat_id': str(chatId),
                        'message_id': str(messageId),
                        'text': str(editText),
                        'parse_mode': 'Markdown'
                    }
                    nuovaRichiesta(urlRic, parRic=parRic)
