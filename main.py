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
                `chat`          INTEGER NOT NULL,
                `tipoRichiesta` TEXT NOT NULL
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


def salvaProv(chatId, tipoRichiesta):
    cursDB.execute(
        '''
        INSERT INTO `provRichieste` (`rfcTime`, `chat`, `tipoRichiesta`)
        VALUES (?, ?, ?);
        ''',
        (rfcTime(), int(chatId), str(tipoRichiesta))
    )
    connDB.commit()


def nuovaRichiesta(urlRichiesta, dati=None):
    try:
        if not dati:
            risposta = requests.get(urlRichiesta)
        else:
            headers = {'Content-Type': 'application/json'}
            risposta = requests.post(
                urlRichiesta,
                headers=headers,
                data=json.dumps(dati)
            )
    except requests.exceptions.ConnectionError:
        salvaErrore('Errore di connessione')
        time.sleep(60)
        risposta = nuovaRichiesta(urlRichiesta, dati)

    if risposta.status_code != 200:
        salvaErrore('Codice non corretto -> ' + str(risposta.status_code))
        time.sleep(60)
        risposta = nuovaRichiesta(urlRichiesta, dati)

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
        + '?chat_id=' + str(chatId) + '&text=' + text
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


def botOnlineText(time):
    return str('Bot *online* da _' + str(time) + ' Secondi_')


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
                    dati = {
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
                    nuovaRichiesta(apiUrl + token + '/sendMessage', dati)
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
                    calcTime = str(minuti) + ' Minuti ' \
                        + str(secondi)
                ore, minuti = divmod(minuti, 60)
                if 'ore' == toTime:
                    calcTime = str(ore) + ' Ore ' \
                        + str(minuti) + ' Minuti ' \
                        + str(secondi)
                giorni, ore = divmod(ore, 24)
                if 'giorni' == toTime:
                    calcTime = str(giorni) + ' Giorni ' \
                        + str(ore) + ' Ore ' \
                        + str(minuti) + ' Minuti ' \
                        + str(secondi)

                if calcTime:
                    editText = botOnlineText(calcTime)
                    urlRichiesta = apiUrl + token + '/editMessageText' \
                        + '?chat_id=' + chatId + '&message_id=' + messageId \
                        + '&text=' + editText + '&parse_mode=Markdown'
                    nuovaRichiesta(urlRichiesta)
