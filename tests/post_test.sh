#!/bin/bash

curl -X POST --upload-file payload.txt \
     http://127.0.0.1:5000/api/post_test
