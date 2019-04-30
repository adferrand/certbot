import os
import shutil
import subprocess
import sys
import tempfile

import pkg_resources
import pytest

BASE_SCRIPTS_PATH = pkg_resources.resource_filename('certbot_integration_tests', 'assets/farm_tests')
SCRIPTS = [path for path in os.listdir(BASE_SCRIPTS_PATH)]
OS_DISTS = ['centos:7', 'ubuntu:16.04', 'ubuntu:18.04']


class IntegrationTestsContext(object):

    def __init__(self, request, letsencrypt_sources):
        self.workspace = tempfile.mkdtemp()
        self.request = request
        self.os_dist = request.param
        self.os_type = self.os_dist.split(':')[0]

        shutil.copytree(letsencrypt_sources, os.path.join(self.workspace, 'letsencrypt'))
        for script in SCRIPTS:
            shutil.copy(os.path.join(BASE_SCRIPTS_PATH, script),
                        os.path.join(self.workspace, os.path.basename(script)))
        self.docker_id = self._launch_docker()

    def _launch_docker(self):
        if hasattr(self.request.config, 'slaveinput'):  # Worker node
            self.worker_id = self.request.config.slaveinput['slaveid']
            acme_xdist = self.request.config.slaveinput['acme_xdist']
        else:  # Primary node
            self.worker_id = 'primary'
            acme_xdist = self.request.config.acme_xdist

        directory_url = acme_xdist['directory_url']
        tls_alpn_01_port = acme_xdist['https_port'][self.worker_id]
        http_01_port = acme_xdist['http_port'][self.worker_id]

        command = ['docker', 'run', '-d', '-it']
        command.extend(['-e', 'DIRECTORY_URL={0}'.format(directory_url)])
        command.extend(['-e', 'TLS_ALPN_01_PORT={0}'.format(tls_alpn_01_port)])
        command.extend(['-e', 'HTTP_01_PORT={0}'.format(http_01_port)])
        command.extend(['-e', 'OS_TYPE={0}'.format(self.os_type)])
        command.extend(['-v', '{0}:/workspace'.format(self.workspace)])
        command.extend(['-w', '/workspace'.format(self.workspace)])
        command.append(self.os_dist)

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
    path = os.path.join(workspace, 'letsencrypt')
    command = ['git', 'clone', 'https://github.com/certbot/certbot.git', path]
    subprocess.check_output(command)
    try:
        yield path
    finally:
        shutil.rmtree(workspace)


@pytest.fixture()
def docker_dist(request, letsencrypt_sources):
    context = IntegrationTestsContext(request, letsencrypt_sources)
    try:
        yield context
    finally:
        context.cleanup()


@pytest.mark.parametrize('docker_dist, script',
                         [(os_dist, script) for script in SCRIPTS for os_dist in OS_DISTS],
                         indirect=['docker_dist'])
def test_hello_world(docker_dist, script):
    docker_dist.exec_in_docker(['./{0}'.format(script)])
