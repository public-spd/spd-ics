#!/usr/bin/env python3

import os
import requests
import datetime
import dateparser
from bs4 import BeautifulSoup
from ics import Calendar, Event

OUTFILE = 'ics/spd-de.ics'
TIMEZONE = 'DE'
REGION = 'DE'
URL = "https://www.spd.de/service/#m75572"
SETTINGS = {
        'RETURN_AS_TIMEZONE_AWARE': True,
        'PREFER_DAY_OF_MONTH': 'current',
        'PREFER_DATES_FROM': 'current_period' }


def split_date(date, region=REGION, languages=[REGION.lower()]):
    parts = [date]
    if '/' in date:
        parts = date.split('/')
    for part in parts[:-1]:
        yield dateparser.parse(part + " ".join(parts[-1].split(" ")[1:]), languages=languages, region=region)
    yield dateparser.parse(parts[-1], languages=languages, region=region)


def parse_time(time, region=REGION, languages=[REGION.lower()]):
    if not time:
        return None
    if 'Uhr' in time:
        tzinfo = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
        time = time.split("Uhr")[0]
        if ':' in time:
            hour_minute = time.split(':')
            return datetime.time(hour=int(hour_minute[0].replace("ab ", "")),
                                 minute=int(hour_minute[1]))
        return datetime.time(hour=int(time), tzinfo=tzinfo)
    try:
        return dateparser.parse(time, languages=languages, region=region, settings=SETTINGS).time()
    except:
        return None


def generate_events(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, features='lxml')

    translation = {'events__item-date': 'date',
                   'events__item-addition': 'time',
                   'events__item-headline': 'name',
                   'events__item-text': 'description',
                   'events__item-cta-link': 'url'}

    for event_element in soup.find_all(class_="events__item-wrapper"):
        event = dict()

        for fr,to in translation.items():
            tmp = event_element.find(class_=fr)

            if not tmp:
                continue

            if to == 'url':
                event[to] = tmp.get('href')
            elif to == 'time':
                event[to] = parse_time(tmp.get_text().replace('ca. ', ''))
            else:
                event[to] = tmp.get_text()
        
        for date in split_date(event['date']):
            yield event|{'date': date}

if __name__ == "__main__":
    contained = set([])
    calendar = Calendar()
    if os.path.exists(OUTFILE):
        with open(OUTFILE, 'r') as f:
            calendar = Calendar("".join(f.readlines()))
            for event in calendar.events:
                contained.add("\t".join([str(event.name), str(event.url)]))

    for event_dict in generate_events(URL):
        if 'date' not in event_dict \
                or not event_dict['date'] \
                or 'time' not in event_dict \
                or not event_dict['time']:
            continue
        begin = datetime.datetime.combine(event_dict['date'],
                                          event_dict['time']) if ('time' in event_dict and event_dict['time']) else event_dict['date']
        event = Event(name=event_dict['name'],
                      begin=begin,
                      duration=datetime.timedelta(hours=1),
                      description="\n".join([event_dict['description'] if 'description' in event_dict else "",
                                             event_dict['url'] if ('url' in event_dict and event_dict['url']) else ""]),
                      url=(event_dict['url'] if ('url' in event_dict and event_dict['url']) else ""))
        if 'time' not in event_dict or not event_dict['time']:
            event.make_all_day()

        if "\t".join([str(event.name), str(event.url)]) not in contained:
            calendar.events.add(event)

    with open(OUTFILE, 'w') as f:
        f.writelines(calendar.serialize_iter())
