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


if __name__ == "__main__":
    # Only for password changing
    # Add args support if a new action needed
    etapadmin_password = input().strip()
    ogretmen_password = input().strip()

    if etapadmin_password:
        p = subprocess.run(
            ["/usr/sbin/chpasswd"], input=f"etapadmin:{etapadmin_password}\n".encode()
        )

        if p.returncode != 0:
            sys.exit(p.returncode)

    if ogretmen_password:
        subprocess.run(
            ["/usr/sbin/chpasswd"], input=f"ogretmen:{ogretmen_password}\n".encode()
        )

        if p.returncode != 0:
            sys.exit(p.returncode)
