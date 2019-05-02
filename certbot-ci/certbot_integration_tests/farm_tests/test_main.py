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

    def __init__(self, request, letsencrypt_sources, docker_envs):
        self.workspace = tempfile.mkdtemp()
        self.os_dist = request.param

        shutil.copytree(letsencrypt_sources, os.path.join(self.workspace, 'letsencrypt'))
        for one_script in SCRIPTS:
            shutil.copy(os.path.join(BASE_SCRIPTS_PATH, one_script),
                        os.path.join(self.workspace, os.path.basename(one_script)))
        self.docker_id = self._launch_docker(request, docker_envs)

    def _launch_docker(self, request, docker_envs):
        if hasattr(request.config, 'slaveinput'):  # Worker node
            worker_id = request.config.slaveinput['slaveid']
            acme_xdist = request.config.slaveinput['acme_xdist']
        else:  # Primary node
            worker_id = 'primary'
            acme_xdist = request.config.acme_xdist

        directory_url = acme_xdist['directory_url']
        tls_alpn_01_port = acme_xdist['https_port'][worker_id]
        http_01_port = acme_xdist['http_port'][worker_id]

        command = ['docker', 'run', '-d', '-it', '--network=host']
        command.extend(['-e', 'DIRECTORY_URL={0}'.format(directory_url)])
        command.extend(['-e', 'TLS_ALPN_01_PORT={0}'.format(tls_alpn_01_port)])
        command.extend(['-e', 'HTTP_01_PORT={0}'.format(http_01_port)])
        command.extend(['-e', 'LE_SUFFIX={0}.wtf'.format(worker_id)])
        command.extend(['-v', '{0}:/workspace'.format(self.workspace)])
        command.extend(['-w', '/workspace'.format(self.workspace)])
        command.append(docker_envs[self.os_dist])

        output = subprocess.check_output(command, universal_newlines=True)
        return output.strip()

    def cleanup(self):
        subprocess.check_output(['docker', 'stop', self.docker_id])
        subprocess.check_output(['docker', 'rm', self.docker_id])
        shutil.rmtree(self.workspace)

    def exec_in_docker(self, args):
        command = ['docker', 'exec', self.docker_id]
        command.extend(args)
        subprocess.check_call(command, stdout=sys.stderr, stderr=subprocess.STDOUT)

    def __repr__(self):
        return 'docker_dist[{0}]'.format(self.os_dist)


@pytest.fixture(scope='module')
def letsencrypt_sources():
    workspace = tempfile.mkdtemp()
    repo_path = os.path.join(workspace, 'letsencrypt')
    command = ['git', 'clone', 'https://github.com/certbot/certbot.git', repo_path,
               '--single-branch', '--depth=1']
    subprocess.check_call(command, stdout=sys.stderr, stderr=subprocess.STDOUT)
    try:
        yield repo_path
    finally:
        shutil.rmtree(workspace)


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
def docker_dist(request, letsencrypt_sources, docker_envs):
    context = IntegrationTestsContext(request, letsencrypt_sources, docker_envs)
    try:
        yield context
    finally:
        context.cleanup()


@pytest.mark.parametrize('docker_dist, letstest_script',
                         [(os_dist, letstest_script) for letstest_script in SCRIPTS for os_dist in OS_DISTS],
                         indirect=['docker_dist'])
def test_hello_world(docker_dist, letstest_script):
    docker_dist.exec_in_docker(['./{0}'.format(letstest_script)])
