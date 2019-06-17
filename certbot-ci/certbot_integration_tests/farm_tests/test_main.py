import os
import shutil
import subprocess
import sys
import tempfile

import pkg_resources
import pytest

BASE_SCRIPTS_PATH = pkg_resources.resource_filename('certbot_integration_tests', 'assets/farm_tests')
BASE_ENV_PATH = pkg_resources.resource_filename('certbot_integration_tests', 'assets/farm_envs')
SCRIPTS = [path for path in os.listdir(BASE_SCRIPTS_PATH)]
OS_DISTS = [config.replace('.Dockerfile', '') for config in os.listdir(BASE_ENV_PATH)]


class IntegrationTestsContext(object):
    """This context fixture handles starting a Docker and run a farm test in it"""
    def __init__(self, request, letsencrypt_auto, docker_envs):
        self.workspace = tempfile.mkdtemp()
        self.os_dist = request.param

        shutil.copy(letsencrypt_auto, os.path.join(self.workspace, 'letsencrypt-auto'))
        shutil.copytree(BASE_SCRIPTS_PATH, os.path.join(self.workspace, 'farm_tests'))
        self.docker_id = self._launch_docker(request, docker_envs)

    def _launch_docker(self, request, docker_envs):
        if hasattr(request.config, 'slaveinput'):  # Worker node
            worker_id = request.config.slaveinput['slaveid']
            acme_xdist = request.config.slaveinput['acme_xdist']
        else:  # Primary node
            worker_id = 'primary'
            acme_xdist = request.config.acme_xdist

        directory_url = acme_xdist['directory_url'].replace('localhost', '172.17.0.1')
        tls_alpn_01_port = acme_xdist['https_port'][worker_id]
        http_01_port = acme_xdist['http_port'][worker_id]

        command = ['docker', 'run', '-d', '-it',
                   '-e', 'DIRECTORY_URL={0}'.format(directory_url),
                   '-e', 'TLS_ALPN_01_PORT={0}'.format(tls_alpn_01_port),
                   '-e', 'HTTP_01_PORT={0}'.format(http_01_port),
                   '-e', 'LE_SUFFIX={0}.wtf'.format(worker_id),
                   '-v', '{0}:/workspace'.format(self.workspace),
                   '-w', '/workspace'.format(self.workspace),
                   '-p', '{0}:{0}'.format(http_01_port),
                   '-p', '{0}:{0}'.format(tls_alpn_01_port),
                   docker_envs[self.os_dist]]

        return subprocess.check_output(command, universal_newlines=True).strip()

    def cleanup(self):
        subprocess.check_output(['docker', 'stop', self.docker_id])
        subprocess.check_output(['docker', 'rm', self.docker_id])
        shutil.rmtree(self.workspace)

    def run_test(self, test_path):
        subprocess.check_call(['docker', 'exec', self.docker_id, os.path.join('farm_tests', test_path)],
                              stdout=sys.stderr, stderr=subprocess.STDOUT)

    def __repr__(self):
        return 'docker_dist[{0}]'.format(self.os_dist)


@pytest.fixture(scope='module')
def letsencrypt_auto(request):
    current_path = str(request.config.rootdir)
    while '.git' not in os.listdir(current_path):
        parent = os.path.dirname(current_path)
        if parent == current_path:
            raise ValueError('Could not find git root path')
        current_path = parent
    yield os.path.join(current_path, 'letsencrypt-auto-source', 'letsencrypt-auto')


@pytest.fixture(scope='module')
def docker_envs():
    config_map = {}
    for dist in OS_DISTS:
        name = '{0}_letstest'.format(dist)
        subprocess.check_call(['docker', 'build', '-f', '{0}.Dockerfile'.format(dist), '-t', name,
                               '--pull', '.'], stdout=sys.stderr, stderr=subprocess.STDOUT, cwd=BASE_ENV_PATH)
        config_map[dist] = name
    yield config_map


@pytest.fixture()
def docker_dist(request, letsencrypt_auto, docker_envs):
    context = IntegrationTestsContext(request, letsencrypt_auto, docker_envs)
    try:
        yield context
    finally:
        context.cleanup()


@pytest.mark.parametrize('docker_dist, letstest_script',
                         [(os_dist, letstest_script) for letstest_script in SCRIPTS for os_dist in OS_DISTS],
                         indirect=['docker_dist'])
def test_hello_world(docker_dist, letstest_script):
    docker_dist.run_test(letstest_script)
