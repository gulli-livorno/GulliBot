import json
import requests
import signal
import time


run = True
startTime = time.time()


def handler_stop_signals(signum, frame):
    global run
    run = False

signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)


token = ""
apiUrl = "https://api.telegram.org/bot"
timeout = 15

urlRichiesta = apiUrl + token + '/getMe'
print(urlRichiesta)
infoBot = requests.get(urlRichiesta)
infoBotDict = json.loads(infoBot.text)
botUsername = infoBotDict['result']['username']


def richiesteLog(rispostaText):
    richiesteLogFile = open('richieste.log', 'a')
    richiesteLogFile.write(rispostaText + '\n')
    richiesteLogFile.close()


def sendMessage(chatId, text):
    urlRichiesta = apiUrl + token + '/sendMessage' \
        '?chat_id=' + chatId + '&text=' + text
    print(urlRichiesta)
    richiesteLog(requests.get(urlRichiesta).text)


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
        break

    try:
        offsetFile = open('offset', 'r')
        offset = int(offsetFile.read())+1
        offsetFile.close()
    except FileNotFoundError:
        offset = -1

    urlRichiesta = apiUrl + token + '/getUpdates' \
        + '?offset=' + str(offset) + '&timeout=' + str(timeout)
    print(urlRichiesta)
    risposta = requests.get(urlRichiesta)
    rispostaDict = json.loads(risposta.text)

    for result in rispostaDict['result']:
        updateId = str(result['update_id'])

        updateLogFile = open('update.log', 'a')
        updateLogFile.write('UPDATE N° ' + updateId + '\n')
        updateLogFile.write(json.dumps(result, indent=4) + '\n')
        updateLogFile.close()

        offsetFile = open('offset', 'w')
        offsetFile.write(updateId)
        offsetFile.close()

        if 'message' in result:
            chatId = str(result['message']['chat']['id'])
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
