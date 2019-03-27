"""
Misc module contains stateless functions that could be used during pytest execution,
or outside during setup/teardown of the integration tests environment.
"""
import contextlib
import errno
import multiprocessing
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from distutils.version import LooseVersion

import requests
from OpenSSL import crypto
from six.moves import socketserver, SimpleHTTPServer


def check_until_timeout(url):
    """
    Wait and block until given url responds with status 200, or raise an exception
    after 150 attempts.
    :param str url: the URL to test
    :raise ValueError: exception raised after 150 unsuccessful attempts to reach the URL
    """
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    for _ in range(0, 150):
        time.sleep(1)
        try:
            if requests.get(url, verify=False).status_code == 200:
                return
        except requests.exceptions.ConnectionError:
            pass

    raise ValueError('Error, url did not respond after 150 attempts: {0}'.format(url))


def find_certbot_root_directory():
    """
    Find the certbot root directory. To do so, this method will recursively move up in the directory
    hierarchy, until finding the git root file, that corresponds to the certbot root directory.
    :return str: the path to the certbot root directory
    """
    script_path = os.path.realpath(__file__)
    current_dir = os.path.dirname(script_path)

    while '.git' not in os.listdir(current_dir) and current_dir != os.path.dirname(current_dir):
        current_dir = os.path.dirname(current_dir)

    dirs = os.listdir(current_dir)
    if '.git' not in dirs:
        raise ValueError('Error, could not find certbot sources root directory')

    return current_dir


def generate_csr(domains, key_path, csr_path, key_type='RSA'):
    """
    Generate a CSR for the given domains, using the provided private key path.
    This method uses the script demo to generate CSR that is available in `examples/generate-csr.py`.
    :param str[] domains: the domain names to include in the CSR
    :param str key_path: path to the private key
    :param str csr_path: path to the CSR that will be generated
    :param str key_type: type of the key (RSA or ECDSA)
    """
    certbot_root_directory = find_certbot_root_directory()
    script_path = os.path.join(certbot_root_directory, 'examples', 'generate-csr.py')

    command = [
        sys.executable, script_path, '--key-path', key_path, '--csr-path', csr_path,
        '--key-type', key_type
    ]
    command.extend(domains)
    subprocess.check_call(command)


def load_sample_data_path(workspace):
    """
    Load the certbot configuration example designed to make OCSP tests, and return its path
    :param str workspace: current test workspace directory path
    :return str: the path to the loaded sample data directory
    """
    certbot_root_directory = find_certbot_root_directory()
    original = os.path.join(certbot_root_directory, 'tests', 'integration', 'sample-config')
    copied = os.path.join(workspace, 'sample-config')
    shutil.copytree(original, copied, symlinks=True)
    return copied


def read_certificate(cert_path):
    """
    Load the certificate from the provided path, and return a human readable version of it (TEXT mode).
    :param str cert_path: the path to the certificate
    :return: the TEXT version of the certificate, as it would be displayed by openssl binary
    """
    with open(cert_path, 'r') as file:
        data = file.read()

    cert = crypto.load_certificate(crypto.FILETYPE_PEM, data.encode('utf-8'))
    return crypto.dump_certificate(crypto.FILETYPE_TEXT, cert).decode('utf-8')


class GracefulTCPServer(socketserver.TCPServer):
    """
    This subclass of TCPServer allows to gracefully reuse an address that has
    just been released by another instance of TCPServer.
    """
    allow_reuse_address = True


@contextlib.contextmanager
def create_http_server(port):
    """
    Setup and start an HTTP server for the given TCP port.
    This server stay active for the lifetime of the context, and is automatically
    stopped with context exit, while its temporary webroot is deleted.
    :param int port: the TCP port to use
    :return str: the temporary webroot attached to this server
    """
    current_cwd = os.getcwd()
    webroot = tempfile.mkdtemp()

    def run():
        GracefulTCPServer(('', port), SimpleHTTPServer.SimpleHTTPRequestHandler).serve_forever()

    process = multiprocessing.Process(target=run)

    try:
        try:
            os.chdir(webroot)
            process.start()
        finally:
            os.chdir(current_cwd)

        check_until_timeout('http://localhost:{0}/'.format(port))

        yield webroot
    finally:
        try:
            if process.is_alive():
                process.terminate()
                process.join()  # Block until process is effectively terminated
        finally:
            shutil.rmtree(webroot)


def list_renewal_hooks_dirs(config_dir):
    """
    Find and return path of all hooks directory for the given certbot config directory
    :param str config_dir: path to the certbot config directory
    :return str[]: list of path to the standard hooks directory for this certbot instance
    """
    renewal_hooks_root = os.path.join(config_dir, 'renewal-hooks')
    return [os.path.join(renewal_hooks_root, item) for item in ['pre', 'deploy', 'post']]


def generate_test_file_hooks(config_dir, hook_probe):
    """
    Create a suite of certbot hooks scripts and put them in the relevant hooks directory
    for the given certbot configuration directory. These scripts, when executed, will write
    specific verbs in the given hook_probe file to allow asserting they have effectively
    been executed.
    :param str config_dir: current certbot config directory
    :param hook_probe: path to the hook probe to test hook scripts execution
    """
    if sys.platform == 'win32':
        extension = 'bat'
    else:
        extension = 'sh'

    renewal_hooks_dirs = list_renewal_hooks_dirs(config_dir)

    for hook_dir in renewal_hooks_dirs:
        try:
            os.makedirs(hook_dir)
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise
        hook_path = os.path.join(hook_dir, 'hook.{0}'.format(extension))
        if extension == 'sh':
            data = '''\
#!/bin/bash -xe
if [ "$0" == "{0}" ]; then
    if [ -z "$RENEWED_DOMAINS" -o -z "$RENEWED_LINEAGE" ]; then
        echo "Environment variables not properly set!" >&2
        exit 1
    fi
fi
echo $(basename $(dirname "$0")) >> "{1}"\
'''.format(hook_path, hook_probe)
        else:
            # TODO: Write the equivalent bat file for Windows
            data = '''\

'''
        with open(hook_path, 'w') as file:
            file.write(data)
        os.chmod(hook_path, os.stat(hook_path).st_mode | stat.S_IEXEC)


def manual_http_hooks(http_server_root):
    """
    Generate suitable http-01 hooks command for test purpose in the given HTTP
    server webroot directory.
    :param str http_server_root: path to the HTTP server configured to serve http-01 challenges
    :return (str, str): a tuple containing the authentication hook and the cleanup hook
    """
    auth = (
        '{0} -c "import os; '
        "challenge_dir = os.path.join('{1}', '.well-known', 'acme-challenge'); "
        'os.makedirs(challenge_dir); '
        "challenge_file = os.path.join(challenge_dir, os.environ.get('CERTBOT_TOKEN')); "
        "open(challenge_file, 'w').write(os.environ.get('CERTBOT_VALIDATION')); "
        '"'
    ).format(sys.executable, http_server_root)
    cleanup = (
        '{0} -c "import os; import shutil; '
        "well_known = os.path.join('{1}', '.well-known'); "
        'shutil.rmtree(well_known); '
        '"'
    ).format(sys.executable, http_server_root)

    return auth, cleanup


def get_certbot_version():
    """
    Find the version of the certbot available in PATH.
    :return str: the certbot version
    """
    output = subprocess.check_output(['certbot', '--version'], universal_newlines=True)
    # Typical response is: output = 'certbot 0.31.0.dev0'
    version_str = output.split(' ')[1].strip()
    return LooseVersion(version_str)
