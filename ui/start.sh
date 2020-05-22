#!/bin/bash

FLASK_APP=dlernen.py FLASK_DEBUG=1 CONFIG=config.Config python -m flask run
