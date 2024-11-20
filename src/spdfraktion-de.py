#!/usr/bin/env python3

import os
import requests
import datetime
import dateparser
from bs4 import BeautifulSoup
from ics import Calendar, Event

OUTFILE = 'ics/spdfraktion-de.ics'
URL = 'https://www.spdfraktion.de/termine?s=&field_date_span_value%5Bdate%5D=&sort_by=created&sort_order=&items_per_page=100'
SETTINGS = {
        'DEFAULT_LANGUAGES': ['de'],
        'PREFER_DATES_FROM': 'future',
        'TIMEZONE': 'Europe/Berlin',
        'RETURN_AS_TIMEZONE_AWARE': True}

def generate_events(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, features='lxml')
    
    for node_termin in soup.find_all('article', class_='node-termin'):
        date_str = node_termin.find_all('span', class_='tag')[0].get_text() + ". "
        date_str += node_termin.find_all('span', class_='monat-jahr')[0].get_text()

        begin, end = date_str.split('-')
        begin = begin.strip()[:-5] + " " + begin.strip()[-5:]
        end = begin[:-5] + end
        name = node_termin.find_all('h4')[0]
        url = name.find('a').get('href')

        yield Event(name=name.get_text(),
                    begin=dateparser.parse(begin, settings=SETTINGS).isoformat(),
                    end=dateparser.parse(end, settings=SETTINGS).isoformat(),
                    description="\n".join([node_termin.find_all('span', class_='participants')[0].get_text(), url],
                    location=node_termin.find_all('span', class_='location')[0].get_text(),
                    url=("" if url.startswith("https://") else "https://spdfraktion.de") + url)

def serialize(event):
    return "\t".join([str(event.name), str(event.begin), str(event.url)])

if __name__ == "__main__":
    contained = set([])
    calendar = Calendar()
    if os.path.exists(OUTFILE):
        with open(OUTFILE, 'r') as f:
            calendar = Calendar("".join(f.readlines()))
            for event in calendar.events:
                contained.add(serialize(event))
    for event in generate_events(URL):
        serialized_event = serialize(event)
        if serialized_event in contained:
            continue
        calendar.events.add(event)
        contained.add(serialized_event)

    with open(OUTFILE, 'w') as f:
        f.writelines(calendar.serialize_iter())
