#!/usr/bin/env python3

import os
import requests
import datetime
import dateparser
from bs4 import BeautifulSoup
from ics import Calendar, Event

OUTFILE = 'ics/spd-dresden-de.ics'
TIMEZONE = 'DE'
REGION = 'DE'
URL = 'https://www.spd-dresden.de/termine/'
SETTINGS = {
        'RETURN_AS_TIMEZONE_AWARE': True,
        'PREFER_DAY_OF_MONTH': 'current',
        'PREFER_DATES_FROM': 'current_period' }


def generate_events(url, region=REGION, languages=[REGION.lower()]):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, features='lxml')
    tzinfo = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo

    for calendar_wrapper in soup.find_all(class_="ics-calendar-list-wrapper"):
        for date_wrapper in calendar_wrapper.find_all(class_="ics-calendar-date-wrapper"):
            date = date_wrapper.find(class_="ics-calendar-date").get_text()
            for events in date_wrapper.find_all("dl", class_="events"):
                times = [dt.get_text() for dt in events.find_all("dt", class_="time")]
                events2 = events.find_all("dd", class_="event")
                for time, event in zip(times, events2):
                    title = event.find_all(class_="title")[0].get_text()
                    try:
                        desc = event.find_all(class_="eventdesc")[0].get_text()
                    except IndexError:
                        desc = None
                    try:
                        loc = event.find_all(class_="location")[0].get_text()
                    except IndexError:
                        loc = None
                    begin = dateparser.parse(" ".join(date.split(" ")[1:]) + ", " + time.split("–")[0].strip(),
                                             languages=languages,
                                             region=region,
                                             settings=SETTINGS)
                    now = datetime.datetime.now(datetime.timezone.utc)
                    if begin < now:
                        begin = begin.replace(year=begin.year + 1)
                    end = dateparser.parse(" ".join(date.split(" ")[1:]) + ", " + time.split("–")[1].strip(),
                                           languages=languages,
                                           region=region,
                                           settings=SETTINGS)
                    if end < now:
                        end = end.replace(year=end.year + 1)
                    description = (desc + "\n") if desc else ""
                    description += ("Link: " + url) if url else ""
                    yield Event(name=title,
                                description=description,
                                location=loc,
                                begin=begin.isoformat(),
                                end=end.isoformat(),
                                url=url)


if __name__ == "__main__":
    contained = set([])
    calendar = Calendar()
    if os.path.exists(OUTFILE):
        with open(OUTFILE, 'r') as f:
            calendar = Calendar("".join(f.readlines()))
            for event in calendar.events:
                contained.add("\t".join([str(event.name), str(event.url)]))

    for event in generate_events(URL):
        if "\t".join([str(event.name), str(event.url)]) not in contained:
            calendar.events.add(event)

    with open(OUTFILE, 'w') as f:
        f.writelines(calendar.serialize_iter())
