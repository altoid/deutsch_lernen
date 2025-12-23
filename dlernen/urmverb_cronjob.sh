#!/bin/bash

cd /Users/dougtomm/src/deutsch_lernen

source venv/bin/activate

cd dlernen

python -m flask --app run app_urmverb update_irregular_verb_wordlist >> /tmp/script_output.log 2>&1

