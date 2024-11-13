ics/:
	mkdir -p ics/

.PHONY ics/*: ics/
	python3 $(@F:.ics=.py)

all: ics/*
