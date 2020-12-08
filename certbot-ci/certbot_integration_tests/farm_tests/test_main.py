import subprocess
from os.path import join, dirname
import sys

import certbot_integration_tests
import pytest
from certbot_integration_tests.certbot_tests import context as certbot_context

CERTBOT_PROJECT_DIR = dirname(dirname(dirname(certbot_integration_tests.__file__)))


class IntegrationTestsContext(certbot_context.IntegrationTestsContext):
    """This context fixture handles starting a Docker and run a farm test in it"""
    def __init__(self, request):
        super(IntegrationTestsContext, self).__init__(request)
        self.subprocess = None

    def run_test(self, docker_image, test_path):
        directory_url = self.directory_url.replace('localhost', '172.17.0.1')

        command = ['docker', 'run', '--rm',
                   '-e', 'DIRECTORY_URL={0}'.format(directory_url),
                   '-e', 'TLS_ALPN_01_PORT={0}'.format(self.tls_alpn_01_port),
                   '-e', 'HTTP_01_PORT={0}'.format(self.http_01_port),
                   '-e', 'LE_SUFFIX={0}.wtf'.format(self.worker_id),
                   '-v', '{0}:/workspace'.format(self.workspace),
                   '-v', '{0}:/certbot'.format(CERTBOT_PROJECT_DIR),
                   '-w', '/workspace',
                   '-p', '{0}:{0}'.format(self.http_01_port),
                   '-p', '{0}:{0}'.format(self.tls_alpn_01_port),
                   docker_image,
                   join('/certbot/certbot-ci/certbot_integration_tests/assets/farm_scripts',
                        test_path)]

        self.subprocess = subprocess.Popen(command, universal_newlines=True, stdout=sys.stderr)
        statuscode = self.subprocess.wait()

        if statuscode != 0:
            raise RuntimeError("Test {0} failed.".format(test_path))

    def cleanup(self):
        self.subprocess.terminate()
        super(IntegrationTestsContext, self).cleanup()


@pytest.mark.parametrize('docker_image, test_name',
                         [(docker_image, test_name)
                          for docker_image in ['ubuntu:18.04']
                          for test_name in ['test_certbot_apache2.sh']])
def test_hello_world(request, docker_image, test_name):
    context = IntegrationTestsContext(request)
    try:
        context.run_test(docker_image, test_name)
    finally:
        context.cleanup()
