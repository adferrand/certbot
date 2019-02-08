#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil


CERTBOT_VERSION = '0.31.0'
CERTBOT_VENV_PATH = '/opt/certbot' if os.name != 'nt' else 'C:\\Certbot\\dist'
VENV_BIN_DIR = 'bin' if os.name != 'nt' else 'Scripts'


def check_certbot_version():
    try:
        process = subprocess.run([os.path.join(CERTBOT_VENV_PATH, VENV_BIN_DIR, 'certbot'),
                                  '--version'], universal_newlines=True,
                                 capture_output=True, check=True)
        return process.stdout.replace('certbot ', '').strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def install_certbot():
    version = check_certbot_version()

    if version != CERTBOT_VERSION:
        sys.stdout.write('Installing/Upgrading Certbot ...')
        sys.stdout.flush()
        if os.path.exists(CERTBOT_VENV_PATH):
            shutil.rmtree(CERTBOT_VENV_PATH)

        subprocess.run(['python', '-m', 'venv', CERTBOT_VENV_PATH], check=True)
        subprocess.run([os.path.join(CERTBOT_VENV_PATH, VENV_BIN_DIR, 'python'),
                        '-m', 'ensurepip', '--upgrade'], check=True)
        subprocess.run([os.path.join(CERTBOT_VENV_PATH, VENV_BIN_DIR, 'pip'),
                       'install', 'certbot'], check=True)
        sys.stdout.write(' done.{0}'.format(os.linesep))
        sys.stdout.flush()


def main(cli_args=sys.argv[1:]):
    exit_code = 0
    install_certbot()

    if cli_args:
        command = [os.path.join(CERTBOT_VENV_PATH, VENV_BIN_DIR, 'certbot')]
        command.extend(cli_args)
        process = subprocess.run(command)
        exit_code = process.returncode

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
