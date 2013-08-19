import subprocess


def run(args):
    return subprocess.Popen(args, stdout=subprocess.PIPE).communicate()
