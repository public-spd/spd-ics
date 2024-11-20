ics/:
	mkdir -p ics/

.PHONY ics/*: ics/
	python3 src/$(@F:.ics=.py)

all: ics/*
