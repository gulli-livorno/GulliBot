import logging
import threading
import os
import requestsAv
import time
import iso8601
import rfc3339
import datetime
import datiBot


def rfcTime(dt=None):
    if not dt:
        dt = datetime.datetime.now()
    return str(rfc3339.rfc3339(dt))


avvioTime = rfcTime()


def infoEvento(evento):
    if 'summary' in evento:
        eventoTot = '*' + evento['summary'] + '*\n'
    else:
        eventoTot = '\[Senza titolo]\n'

    if 'description' in evento:
        eventoTot += evento['description'] + '\n'

    if 'date' in evento['start']:
        inizio = iso8601.parse_date(evento['start']['date'])
        fine = iso8601.parse_date(evento['end']['date'])
        if inizio.day == fine.day-1:
            eventoTot += inizio.strftime("%d/%m/%Y\n")
        else:
            eventoTot += inizio.strftime("_Dal_\n%d/%m/%Y\n")
            eventoTot += fine.strftime("_Al_\n%d/%m/%Y\n")
    elif 'dateTime' in evento['start']:
        inizio = iso8601.parse_date(evento['start']['dateTime'])
        fine = iso8601.parse_date(evento['end']['dateTime'])
        if inizio.day == fine.day:
            eventoTot += inizio.strftime("_%d/%m/%Y_\n%H:%M - ")
            eventoTot += fine.strftime("%H:%M\n")
        else:
            eventoTot += inizio.strftime("_Dal_\n%d/%m/%Y %H:%M\n")
            eventoTot += fine.strftime("_Al_\n%d/%m/%Y %H:%M\n")

    return eventoTot


class elaboraUpd(threading.Thread):
    def sendMessage(self, text, markdown=False, rimKey=False):
        data = {
            'chat_id': self.update['message']['chat']['id'],
            'text': text
        }
        if markdown:
            data['parse_mode'] = 'Markdown'
        if rimKey:
            data['reply_markup'] = {
                'remove_keyboard': True
            }
        requestsAv.post('telegram', '/sendMessage', data=data)

    def sendReplyKey(self, text, replyList):
        keyboard = []
        for replyText in replyList:
            keyboard.append([{'text': replyText}])
        data = {
            'chat_id': self.update['message']['chat']['id'],
            'text': text,
            'parse_mode': 'Markdown',
            'reply_markup':
            {
                'keyboard': keyboard,
                'resize_keyboard': True,
                'one_time_keyboard': True,
                'force_reply': True
            }
        }
        requestsAv.post('telegram', '/sendMessage', data=data)

    def scritturaCmd(self, comando=None):
        self.db.eseg(
            '''
                UPDATE `chat`
                SET `comando`=?
                WHERE `id`=?;
            ''',
            (comando, int(self.update['message']['chat']['id']))
        )
        logging.debug('Scrittura comando effettuata')

    def eventiCmd(self):
        text = self.update['message']['text']

        giorni = -1
        if text == 'Settimana':
            giorni = 7
        elif text == 'Mese':
            giorni = 30
        elif text == 'Tutti':
            giorni = 0
        else:
            self.sendMessage('Periodo non consentito')

        if giorni != -1:
            params = {
                'timeMin': rfcTime(),
                'singleEvents': True,
                'orderBy': 'startTime'
            }
            if giorni != 0:
                dtFine = datetime.datetime.now() + \
                    datetime.timedelta(days=giorni)
                params['timeMax'] = rfcTime(dtFine)

            err, risposta = requestsAv.get(
                'googleCalendar', '/events',
                params=params
            )
            if not err:
                eventiDict = risposta.json()
                if len(eventiDict['items']) > 0:
                    for evento in eventiDict['items']:
                        self.sendMessage(
                            infoEvento(evento),
                            markdown=True,
                            rimKey=True
                        )
                else:
                    self.sendMessage(
                        '*Nessun evento in programma*',
                        markdown=True,
                        rimKey=True
                    )
            else:
                logging.error(err)
            self.scritturaCmd()

    def eventiRisp(self):
        self.sendReplyKey(
            'Visualizza eventi in questa/o',
            ['Settimana', 'Mese', 'Tutti']
        )
        self.scritturaCmd('eventi')

    def inventarioCmd(self, sheetTab):
        hwId = str(self.update['message']['text'].split(' ')[0])[1:]
        logging.debug(hwId)
        datiHw = cachedSheet[sheetTab][int(hwId)+1]
        msgDati = ''
        letturaDati = 0
        while letturaDati < len(datiHw):
            msgDati += '{}: {}\n'.format(
                cachedSheet[sheetTab][0][letturaDati], datiHw[letturaDati]
            )
            letturaDati += 1
        logging.debug(msgDati)
        self.sendMessage(msgDati, rimKey=True)
        self.scritturaCmd()

    def inventarioRisp(self, passo):
        if passo == 1:
            err, risposta = requestsAv.get('googleSheet')
            if not err:
                replyList = []
                for sheet in risposta.json()['sheets']:
                    logging.debug(sheet['properties']['title'])
                    replyList.append(sheet['properties']['title'])
                self.sendReplyKey(
                    'Quale inventario ti devo mostrare?',
                    replyList
                )
                self.scritturaCmd('inventario1')
        elif passo == 2:
            err, risposta = requestsAv.get(
                'googleSheet', '/values/' + self.update['message']['text']
            )
            if err:
                self.sendMessage('Input non consentito')
            else:
                sheetValues = risposta.json()['values']
                global cachedSheet
                cachedSheet = {}
                cachedSheet[self.update['message']['text']] = sheetValues
                hwList = []
                rowIncr = 0
                for value in sheetValues[1:]:
                    try:
                        hwList.append('\{} ID={} > {}'.format(
                            rowIncr, value[0], value[1])
                        )
                    except IndexError:
                        hwList.append('\{} Senza nome'.format(rowIncr))
                    rowIncr += 1
                self.sendReplyKey('Seleziona un pc:', hwList)
                self.scritturaCmd(
                    'inventario2:' + self.update['message']['text']
                )

    def notificheCmd(self):
        text = self.update['message']['text']

        attiva = None
        if text == 'Attiva':
            attiva = 'si'
        elif text == 'Disattiva':
            attiva = 'no'
        else:
            self.sendMessage('Opzione non consentita')

        if attiva:
            self.sendMessage(
                'Preferenza salvata',
                rimKey=True
            )
            self.scritturaCmd()
            self.db.eseg(
                '''
                    UPDATE `chat`
                    SET `notifiche`=?
                    WHERE `id`=?;
                ''',
                (attiva, int(self.update['message']['chat']['id']))
            )
            logging.debug('Scrittura pref. notifiche')

    def notificheRisp(self):
        selNotifiche = self.db.eseg(
            '''
                SELECT `notifiche`
                FROM `chat`
                WHERE `id`=?;
            ''',
            (int(self.update['message']['chat']['id']),),
            'one'
        )[0]

        self.sendReplyKey(
            'Notifiche attive: *' + selNotifiche + '*',
            ['Attiva', 'Disattiva']
        )
        self.scritturaCmd('notifiche')

    def inoltraCmd(self, orarioInoltro):
        self.sendMessage(
            'Inoltro salvato',
            rimKey=True
        )
        self.scritturaCmd()
        self.db.eseg(
            'INSERT INTO `inoltro` VALUES (?,?);',
            (
                orarioInoltro,
                self.update['message']['text']
            )
        )
        logging.debug('Scrittura pref. notifiche')

    def inoltraRisp(self, passo):
        if passo == 1:
            if self.update['message']['chat']['id'] not in datiBot.adminIDs:
                self.sendMessage('Comando non permesso')
            else:
                self.sendMessage('Inviami l\'orario')
                self.scritturaCmd('inoltra1')
        elif passo == 2:
            ogg = datetime.datetime.now().strftime("%Y%m%d")
            orarioInoltro = self.update['message']['text'].replace('oggi', ogg)
            self.sendMessage('Inviami il messaggio')
            self.scritturaCmd('inoltra2:' + orarioInoltro)

    def verificaCmd(self, comando):
        msgText = self.update['message']['text']
        if (msgText == comando) or (msgText == comando+'@'+datiBot.username):
            return True
        else:
            return False

    def __init__(self, name=None, update=None, db=None):
        super(elaboraUpd, self).__init__(name=name)
        self.update = update
        self.db = db

    def run(self):
        logging.debug(self.update['update_id'])

        qDati = self.db.eseg(
            '''
                SELECT `comando`
                FROM `chat`
                WHERE `id`=?;
            ''',
            (int(self.update['message']['chat']['id']),),
            'one'
        )
        memCmd = qDati[0] if qDati else None

        logging.debug(memCmd)
        if memCmd:
            if 'message' in self.update and 'text' in self.update['message']:
                if self.verificaCmd('/annulla'):
                    self.sendMessage('Comando annullato', rimKey=True)
                    self.scritturaCmd()
                else:
                    if memCmd == 'eventi':
                        self.eventiCmd()
                    if memCmd == 'inventario1':
                        self.inventarioRisp(2)
                    elif memCmd.startswith('inventario2:'):
                        self.inventarioCmd(memCmd.split(':')[1])
                    elif memCmd == 'notifiche':
                        self.notificheCmd()
                    elif memCmd == 'inoltra1':
                        self.inoltraRisp(2)
                    elif memCmd.startswith('inoltra2:'):
                        self.inoltraCmd(memCmd.split(':')[1])
                    else:
                        logging.error('Comando interno errato')
            else:
                self.sendMessage('Input non consentito')
        else:
            if 'message' in self.update and 'text' in self.update['message']:
                if self.verificaCmd('/aiuto') or self.verificaCmd('/start'):
                    cmdAiutoFile = open('cmdAiuto.txt', 'r')
                    self.sendMessage(str(cmdAiutoFile.read()))
                    cmdAiutoFile.close()
                elif self.verificaCmd('/eventi'):
                    self.eventiRisp()
                elif self.verificaCmd('/inventario'):
                    self.inventarioRisp(1)
                elif self.verificaCmd('/notifiche'):
                    self.notificheRisp()
                elif self.verificaCmd('/info'):
                    self.sendMessage(
                        'Avvio: {}\nVersione: {}'.format(
                            avvioTime, datiBot.versione
                        )
                    )
                elif self.verificaCmd('/chatid'):
                    self.sendMessage(self.update['message']['chat']['id'])
                elif self.verificaCmd('/inoltra'):
                    self.inoltraRisp(1)
                else:
                    self.sendMessage('Comando non trovato')

        if 'message' in self.update:
            chat = self.update['message']['chat']

            self.db.eseg(
                '''
                    INSERT OR IGNORE
                    INTO `chat`(`id`,`tipo`,`creata`)
                    VALUES (?,?,?);
                ''',
                (int(chat['id']), chat['type'], rfcTime()),
            )
            logging.debug('Query dati chat')

            titolo = chat['title'] if 'title' in chat else None
            username = chat['username'] if 'username' in chat else None
            nome = chat['first_name'] if 'first_name' in chat else None
            cogn = chat['last_name'] if 'last_name' in chat else None
            self.db.eseg(
                '''
                    UPDATE `chat`
                    SET `titolo`=?, `username`=?,
                        `nome`=?, `cognome`=?,
                        `aggiornata`=?, `accessi`=`accessi`+1
                    WHERE `id`=?;
                ''',
                (
                    titolo, username,
                    nome, cogn,
                    rfcTime(), int(chat['id'])
                )
            )
            logging.debug('Query info chat')


class threadArrivi(threading.Thread):
    def __init__(self, name=None, db=None):
        super(threadArrivi, self).__init__(name=name)
        self.db = db
        self.offset = '-1'

    def run(self):
        while os.path.isfile('script.run'):
            time.sleep(1)  # Cancellare in prodizione

            err, risposta = requestsAv.get(
                'telegram', '/getUpdates',
                params={
                    'offset': self.offset,
                    'timeout': '30'
                }
            )
            if not err:
                rispostaJson = risposta.json()
                if rispostaJson['ok']:
                    for update in rispostaJson['result']:
                        self.offset = str(int(update['update_id'])+1)
                        elaboraUpd(
                            name='Update: ' + str(update['update_id']),
                            update=update,
                            db=self.db
                        ).start()
            else:
                logging.error(err)
                time.sleep(30)
        else:
            self.db.close()
