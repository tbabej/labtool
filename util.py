import os
import subprocess


def run(args):
    child = subprocess.Popen(args, stdout=subprocess.PIPE)
    stdout, stderr = child.communicate()
    rc = child.returncode

    return stdout, stderr, rc


def require_root():
    if os.geteuid() != 0:
        raise RuntimeError("You need to run this script as a root.")
