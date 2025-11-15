#!/bin/bash

# flask run ignores configured server_name.  it defaults to 127.0.0.1:5000 so have to set it here.
FLASK_APP=run FLASK_DEBUG=1 python -m flask run --host=0.0.0.0 --port 8000

