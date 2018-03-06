import logging
import threading
import os
import requestsAv
import time
import iso8601
import rfc3339
import datetime
import datiBot

dbSemaphore = threading.BoundedSemaphore(value=1)


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
                'google', '/events',
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
        data = {
            'chat_id': self.update['message']['chat']['id'],
            'text': 'Visualizza eventi in questa/o',
            'reply_markup':
            {
                'keyboard': [
                    [{'text': 'Settimana'}],
                    [{'text': 'Mese'}],
                    [{'text': 'Tutti'}]
                ],
                'resize_keyboard': True,
                'one_time_keyboard': True,
                'force_reply': True
            }
        }
        requestsAv.post('telegram', '/sendMessage', data=data)
        self.scritturaCmd('eventi')

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

        data = {
            'chat_id': self.update['message']['chat']['id'],
            'text': 'Notifiche attive: *' + selNotifiche + '*',
            'parse_mode': 'Markdown',
            'reply_markup':
            {
                'keyboard': [
                    [{'text': 'Attiva'}],
                    [{'text': 'Disattiva'}]
                ],
                'resize_keyboard': True,
                'one_time_keyboard': True,
                'force_reply': True
            }
        }
        requestsAv.post('telegram', '/sendMessage', data=data)
        self.scritturaCmd('notifiche')

    def inoltraCmd(self):
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

    def inoltraRisp(self, cont=None):
        if not cont:
            if self.update['message']['chat']['id'] not in datiBot.adminIDs:
                self.sendMessage('Comando non permesso')
            else:
                self.sendMessage('Inviami l\'orario')
                self.scritturaCmd('inoltra1')
        else:
            global orarioInoltro
            ogg = datetime.datetime.now().strftime("%Y%m%d")
            orarioInoltro = self.update['message']['text'].replace('oggi', ogg)
            self.sendMessage('Inviami il messaggio')
            self.scritturaCmd('inoltra2')

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
                    elif memCmd == 'notifiche':
                        self.notificheCmd()
                    elif memCmd == 'inoltra1':
                        self.inoltraRisp(True)
                    elif memCmd == 'inoltra2':
                        self.inoltraCmd()
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
                    self.inoltraRisp()
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
