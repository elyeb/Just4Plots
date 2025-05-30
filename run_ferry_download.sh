#!/bin/bash

# Set PATH to include directories for Python and GeckoDriver
export PATH=/Library/Frameworks/Python.framework/Versions/3.9/bin

/usr/bin/caffeinate -i /Library/Frameworks/Python.framework/Versions/3.9/bin/python3 /Users/elyebliss/Documents/Just4Plots/src/ferry_delays_db_update.py >> /Users/elyebliss/Documents/Just4Plots/ferry_download.log 2>&1
