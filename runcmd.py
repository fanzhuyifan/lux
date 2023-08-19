import shlex, subprocess

def run_cmd(cmd, bg=False):
    args = shlex.split(cmd)
    ret = subprocess.check_output(args)
    return ret