#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List

import requests
from atoma import parse_atom_bytes
from atoma.atom import AtomEntry
from api import clean_html
from const import ATOM_FEED


def lista_articoli(entries: List[AtomEntry]) -> list:
    a_list = []
    for art in entries:
        articolo = {
            'titolo': clean_html(art.title.value),
            'descrizione': clean_html(art.summary.value),
            'pubblicazione': art.published
        }
        for l in art.links:
            if l.type_ == 'text/html':
                articolo['link'] = l.href
                break
        a_list.append(articolo)
    return a_list


def scarica_feed() -> list:
    r = requests.get(ATOM_FEED)
    if r.status_code == 200:
        return lista_articoli(parse_atom_bytes(r.content).entries)
    else:
        return []
