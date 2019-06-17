import os
import shutil
import subprocess
import sys
import tempfile

import pkg_resources
import pytest

from certbot_integration_tests.farm_tests.conftest import OS_DISTS

BASE_SCRIPTS_PATH = pkg_resources.resource_filename('certbot_integration_tests', 'assets/farm_tests')
SCRIPTS = [path for path in os.listdir(BASE_SCRIPTS_PATH)]


class IntegrationTestsContext(object):
    """This context fixture handles starting a Docker and run a farm test in it"""
    def __init__(self, request):
        self._workspace = tempfile.mkdtemp()
        self._request = request

        self._prepare_letsencrypt_and_scripts()
        self._docker_id = self._launch_docker()

    def _launch_docker(self,):
        if hasattr(self._request.config, 'slaveinput'):  # Worker node
            worker_id = self._request.config.slaveinput['slaveid']
            acme_xdist = self._request.config.slaveinput['acme_xdist']
        else:  # Primary node
            worker_id = 'primary'
            acme_xdist = self._request.config.acme_xdist

        directory_url = acme_xdist['directory_url'].replace('localhost', '172.17.0.1')
        tls_alpn_01_port = acme_xdist['https_port'][worker_id]
        http_01_port = acme_xdist['http_port'][worker_id]

        command = ['docker', 'run', '-d', '-it',
                   '-e', 'DIRECTORY_URL={0}'.format(directory_url),
                   '-e', 'TLS_ALPN_01_PORT={0}'.format(tls_alpn_01_port),
                   '-e', 'HTTP_01_PORT={0}'.format(http_01_port),
                   '-e', 'LE_SUFFIX={0}.wtf'.format(worker_id),
                   '-v', '{0}:/workspace'.format(self._workspace),
                   '-w', '/workspace'.format(self._workspace),
                   '-p', '{0}:{0}'.format(http_01_port),
                   '-p', '{0}:{0}'.format(tls_alpn_01_port),
                   '--network', 'host',
                   '{0}_letstest'.format(self._request.param)]

        return subprocess.check_output(command, universal_newlines=True).strip()

    def _prepare_letsencrypt_and_scripts(self):
        current_path = str(self._request.config.rootdir)
        while '.git' not in os.listdir(current_path):
            parent = os.path.dirname(current_path)
            if parent == current_path:
                raise ValueError('Could not find git root path')
            current_path = parent

        shutil.copy(os.path.join(current_path, 'letsencrypt-auto-source', 'letsencrypt-auto'),
                    os.path.join(self._workspace, 'letsencrypt-auto'))
        shutil.copytree(BASE_SCRIPTS_PATH, os.path.join(self._workspace, 'farm_tests'))

    def cleanup(self):
        subprocess.check_output(['docker', 'stop', self._docker_id])
        subprocess.check_output(['docker', 'rm', self._docker_id])
        shutil.rmtree(self._workspace)

    def run_test(self, test_path):
        subprocess.check_call(['docker', 'exec', self._docker_id, os.path.join('farm_tests', test_path)],
                              stdout=sys.stderr, stderr=subprocess.STDOUT)

    def __repr__(self):
        return 'docker_dist[{0}]'.format(self.os_dist)


@pytest.fixture()
def docker_dist(request):
    context = IntegrationTestsContext(request)
    try:
        yield context
    finally:
        context.cleanup()


@pytest.mark.parametrize('docker_dist, letstest_script',
                         [(os_dist, letstest_script) for letstest_script in SCRIPTS for os_dist in OS_DISTS],
                         indirect=['docker_dist'])
def test_hello_world(docker_dist, letstest_script):
    docker_dist.run_test(letstest_script)
