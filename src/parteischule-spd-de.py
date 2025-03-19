#!/usr/bin/env python3

# on seminare

import re
import os
import requests
import datetime
from bs4 import BeautifulSoup
from ics import Calendar, Event

OUTFILE = 'ics/parteischule-spd-de.ics'
TIMEZONE = 'DE'
REGION = 'DE'
URL = "https://parteischule.spd.de/?modul=businessstartseite&Id=149424#Tab-Kategorien"
SETTINGS = {
        'RETURN_AS_TIMEZONE_AWARE': True,
        'PREFER_DAY_OF_MONTH': 'current',
        'PREFER_DATES_FROM': 'current_period' }

DATE_TIME = re.compile(r'(?P<dd>[0-9]{2})\.(?P<MM>[0-9]{2})\.(?P<yyyy>[0-9]{4}) (?P<hh>[0-9]{2}):(?P<mm>[0-9]{2})( - (?P<hh2>[0-9]{2}):(?P<mm2>[0-9]{2}))?')


def generate_events(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, features='lxml')

    for event_element in soup.find_all("div", class_="mecEnTermin"):
        content_container = event_element.find_all("div", class_="ContentContainer")[0]
        name = content_container.find_all("h2")[0].text
        date_from_until = content_container.find_all("span", class_="mecEnFormatSmall")[0].text

        m = DATE_TIME.search(date_from_until)
        begin = datetime.datetime(day=int(m.group("dd")),
                                  month=int(m.group("MM")),
                                  year=int(m.group("yyyy")),
                                  hour=int(m.group("hh")),
                                  minute=int(m.group("mm")))
        duration = datetime.timedelta(hours=1)
        if m.group("mm2") is not None:
            duration = datetime.timedelta(hours=int(m.group("hh2"))-begin.hour, minutes=int(m.group("mm2"))-begin.hour)

        event = Event(name=name,
                      begin=begin.isoformat(),
                      duration=duration,
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
