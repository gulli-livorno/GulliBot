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
rawUpdateCyc = 1

if not dbEsiste:
    cursDB.execute(
        '''
            CREATE TABLE `rawUpdate` (
                `id`            INTEGER NOT NULL UNIQUE,
                `rfcTime`       TEXT NOT NULL,
                `urlTg`         TEXT NOT NULL,
                `updateText`    TEXT NOT NULL
            );
        '''
    )
    connDB.commit()
    cursDB.execute(
        '''
            CREATE TABLE `provRichieste` (
                `id`            INTEGER PRIMARY KEY AUTOINCREMENT,
                `rfcTime`       TEXT NOT NULL,
                `chat`          INTEGER NOT NULL
            );
        '''
    )
    connDB.commit()
    cursDB.execute(
        '''
            CREATE TABLE `errori` (
                `id`            INTEGER PRIMARY KEY AUTOINCREMENT,
                `rfcTime`       TEXT NOT NULL,
                `tipoErrore`    TEXT NOT NULL
            );
        '''
    )
    connDB.commit()
    for rowInt in range(1, 11):
        cursDB.execute(
            '''
            INSERT INTO `rawUpdate` (`id`, `rfcTime`, `urlTg`, `updateText`)
            VALUES (?, ?, ?, ?);
            ''',
            (rowInt, str(rowInt), str(rowInt), str(rowInt))
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
        '''
        INSERT INTO `errori` (`rfcTime`, `tipoErrore`)
        VALUES (?, ?);
        ''',
        (rfcTime(), str(tipoErrore))
    )
    connDB.commit()


def nuovaRichiesta(urlRichiesta):
    try:
        risposta = requests.get(urlRichiesta)
    except requests.exceptions.ConnectionError:
        salvaErrore('Errore di connessione')
        time.sleep(60)
        risposta = nuovaRichiesta(urlRichiesta)

    global rawUpdateCyc
    if rawUpdateCyc > 10:
        rawUpdateCyc = 1
    cursDB.execute(
        '''
        UPDATE `rawUpdate`
        SET `rfcTime`=?, `urlTg`=?, `updateText`=?
        WHERE `id`=?;
        ''',
        (rfcTime(), str(urlRichiesta), str(risposta.text), int(rawUpdateCyc))
    )
    connDB.commit()
    rawUpdateCyc += 1

    return risposta


def sendMessage(chatId, text):
    urlRichiesta = apiUrl + token + '/sendMessage' \
        '?chat_id=' + chatId + '&text=' + text
    nuovaRichiesta(urlRichiesta)


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


while True:
    if not run:
        offsetFile = open('offset', 'w')
        offsetFile.write(str(offset))
        offsetFile.close()

        cursDB.close()
        connDB.close()

        break

    urlRichiesta = apiUrl + token + '/getUpdates' \
        + '?offset=' + str(offset) + '&timeout=' + str(timeout)
    rispostaDict = json.loads(nuovaRichiesta(urlRichiesta).text)

    for result in rispostaDict['result']:
        offset = int(result['update_id'])+1

        if 'message' in result:
            chatId = str(result['message']['chat']['id'])
            cursDB.execute(
                '''
                INSERT INTO `provRichieste` (`rfcTime`, `chat`)
                VALUES (?, ?);
                ''',
                (rfcTime(), int(chatId))
            )
            connDB.commit()

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
                    sendMessage(
                        chatId,
                        'Bot online da ' + secUptime + ' secondi'
                    )
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
