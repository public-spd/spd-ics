ics/:
	mkdir -p ics/

ics/spd-de.ics: ics/
	python3 spd-de.py

ics/spd-dresden-de.ics: ics/
	python3 spd-dresden-de.py

all: ics/spd-de.ics ics/spd-dresden-de.ics
