#!/usr/bin/env python3

import os
import requests
import datetime
import dateparser
from bs4 import BeautifulSoup
from ics import Calendar, Event

OUTFILE = 'ics/spd-de-ueber-uns-onlinekonferenz.ics'
TIMEZONE = 'DE'
REGION = 'DE'
URL = "https://www.spd.de/ueber-uns/onlinekonferenz"
SETTINGS = {
        'RETURN_AS_TIMEZONE_AWARE': True,
        'PREFER_DAY_OF_MONTH': 'current',
        'PREFER_DATES_FROM': 'current_period' }


def generate_events(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, features='lxml')

    for event_element in soup.find_all("h2", class_="text__headline"):
        print(event_element.text)
        begin = dateparser.parse(event_element.text.split(" den ")[-1], settings=SETTINGS)
        event = Event(name=event_element.text,
                      begin=begin.isoformat(),
                      duration=datetime.timedelta(hours=1),
                      description="\n".join([event_element.text, url]),
                      url=url)

        yield event

if __name__ == "__main__":
    contained = set([])
    calendar = Calendar()
    if os.path.exists(OUTFILE):
        with open(OUTFILE, 'r') as f:
            old_calendar = Calendar("".join(f.readlines()))
            for event in old_calendar.events:
                contained.add("\t".join([str(event.name), str(event.url)]))
                calendar.events.add(event)

    for event in generate_events(URL):
        if "\t".join([str(event.name), str(event.url)]) not in contained:
            calendar.events.add(event)

    with open(OUTFILE, 'w') as f:
        f.writelines(calendar.serialize_iter())
