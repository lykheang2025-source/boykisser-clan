#!/usr/bin/env python3
"""True daemon launcher - fully detaches from parent process"""
import os
import sys

def daemonize():
    """Double-fork daemonization"""
    # First fork - detach from parent
    pid = os.fork()
    if pid > 0:
        # Parent process - exit immediately
        return  # Don't sys.exit, just return so we can print PID

    # Child process - become session leader
    os.setsid()

    # Second fork - fully detach
    pid2 = os.fork()
    if pid2 > 0:
        # Exit second parent
        os._exit(0)

    # We're now a true daemon
    # Change working directory
    os.chdir('/workspaces/boykisser-clan')

    # Redirect file descriptors
    devnull = os.open(os.devnull, os.O_RDWR)
    os.dup2(devnull, 0)  # stdin
    os.dup2(devnull, 1)  # stdout
    os.dup2(devnull, 2)  # stderr
    os.close(devnull)

    return True

if __name__ == "__main__":
    first_pid = os.fork()
    if first_pid > 0:
        # Print the PID of the intermediate process
        print(first_pid)
        sys.exit(0)

    # Grandchild - continue daemonizing
    os.setsid()
    pid2 = os.fork()
    if pid2 > 0:
        os._exit(0)

    # Fully detached daemon
    os.chdir('/workspaces/boykisser-clan')

    # Open log file
    import io
    log_fd = os.open('bot_output.log', os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    os.dup2(log_fd, 1)
    os.dup2(log_fd, 2)
    os.close(log_fd)

    # Close stdin
    devnull = os.open(os.devnull, os.O_RDONLY)
    os.dup2(devnull, 0)
    os.close(devnull)

    # Execute bot.py
    os.execvp('python3', ['python3', '-u', 'bot.py'])
