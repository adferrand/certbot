import subprocess


def test_it():
    subprocess.check_call(['letsencrypt-auto', '-v', '-n', '--debug', '--version'])
