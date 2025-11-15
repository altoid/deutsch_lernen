#!/bin/bash

# The flask run command, which utilizes Flask's built-in development
# server, does not directly use the SERVER_NAME configuration for
# binding the host and port. While SERVER_NAME is important for
# features like subdomain matching and URL generation within an
# application context, the flask run command prioritizes explicitly
# provided host and port arguments or defaults to 127.0.0.1:5000 if
# none are specified.
# 
# SERVER_NAME's Primary Role: The SERVER_NAME configuration in Flask
# is primarily designed for:
# 
# Subdomain Matching: Enabling the application to recognize and handle
# requests on different subdomains (e.g., sub.example.com).
#
# URL Generation: Assisting Flask in generating correct external URLs
# when no request context is available.
# 
# Session Cookies: Influencing how session cookies are handled,
# especially in subdomain scenarios.
# 
# flask run's Behavior: The flask run command, which wraps Werkzeug's
# run_simple function, determines the host and port based on
# command-line arguments: If you provide --host and --port arguments
# (e.g., flask run --host=0.0.0.0 --port=8000), these will be used.
# 
# If no host and port are specified, it defaults to 127.0.0.1:5000.
# so we need to set these here.

FLASK_APP=run FLASK_DEBUG=1 python -m flask run --host=0.0.0.0 --port 8000

