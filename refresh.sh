#!/bin/zsh
# Daily refresh: pull data, rebuild index.html. Logs to data/refresh.log
cd "$(dirname "$0")"
{
  echo "=== $(date -u '+%Y-%m-%d %H:%M UTC')"
  /usr/bin/python3 -I pull.py && /usr/bin/python3 -I build.py
} >> data/refresh.log 2>&1
