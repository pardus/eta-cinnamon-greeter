#!/usr/bin/python3
import os
import subprocess
import sys


def run(cmd="", capture_output=False, input=None):
    return subprocess.run(
        ["pkexec", os.path.abspath(__file__), cmd],
        capture_output=capture_output,
        input=input,
    )


def _change_password(uid, username, password):
    # Create password hash
    p = subprocess.run(
        ["/usr/bin/openssl", "passwd", "-6", password], capture_output=True, text=True
    )
    if p.returncode != 0:
        sys.exit(p.returncode)

    hashed_password = p.stdout.strip()

    # Change user password with hashed value
    p2 = subprocess.run(["/usr/sbin/usermod", "-p", hashed_password, username])
    if p2.returncode != 0:
        sys.exit(p2.returncode)


if __name__ == "__main__":
    # Only for password changing
    # Add args support if a new action needed
    etapadmin_password = input().strip()
    ogretmen_password = input().strip()

    if etapadmin_password:
        _change_password(1000, "etapadmin", etapadmin_password)

    if ogretmen_password:
        _change_password(1001, "ogretmen", ogretmen_password)
