import logging
import threading
import os
import requestsAv
import time
import datetime


class threadPartenze(threading.Thread):
    def __init__(self, name=None, db=None):
        super(threadPartenze, self).__init__(name=name)
        self.db = db
        self.name = name

    def run(self):
        while os.path.isfile('script.run'):
            oraAtt = datetime.datetime.now().strftime("%Y%m%d-%H%M")
            logging.debug(oraAtt)
            msgInol = self.db.eseg(
                'SELECT `testo`,`_rowid_` FROM `inoltro` WHERE `orario`<=?',
                (oraAtt,),
                'all'
            )
            for msg in msgInol:
                ricNot = self.db.eseg(
                    'SELECT `id` FROM `chat` WHERE `notifiche`=\'si\'',
                    recDati='all'
                )
                for chatid in ricNot:
                    data = {
                        'chat_id': int(chatid[0]),
                        'text': msg[0]
                    }
                    requestsAv.post('telegram', '/sendMessage', data=data)
                self.db.eseg(
                    'DELETE FROM `inoltro` WHERE `_rowid_`=?',
                    (int(msg[1]),)
                )
            time.sleep(30)
        else:
            self.db.close()
