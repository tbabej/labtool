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


def normalize_hostname(ip):
    last_ip_segment = ip.split('.')[-1]

    if len(last_ip_segment) == 1:
        return 'vm-00%s' % last_ip_segment
    elif len(last_ip_segment) == 2:
        return 'vm-0%s' % last_ip_segment
    else:
        return 'vm-%s' % last_ip_segment
