#!/bin/bash

cd /usr/src/app
pip install --no-cache-dir -q -r requirements.txt
pip install ./pylyngdorflib
python intg-lyngdorf/driver.py