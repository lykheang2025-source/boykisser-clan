#!/usr/bin/env python3
"""Daemon to keep the Discord bot running"""
import subprocess
import sys
import os
import time

os.chdir(os.path.dirname(os.path.abspath(__file__)))

log = open("bot_output.log", "a")
log.write(f"\n--- Starting bot at {time.ctime()} ---\n")
log.flush()

proc = subprocess.Popen(
    [sys.executable, "-u", "bot.py"],
    stdout=log,
    stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL
)

print(f"Bot started with PID: {proc.pid}")
sys.exit(0)
