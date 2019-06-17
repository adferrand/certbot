import pkg_resources
import os
import subprocess

from certbot_integration_tests.conftest import _print_on_err

BASE_ENV_PATH = pkg_resources.resource_filename('certbot_integration_tests', 'assets/farm_envs')
OS_DISTS = [config.replace('.Dockerfile', '') for config in os.listdir(BASE_ENV_PATH)]


def pytest_configure(config):
    if not hasattr(config, 'slaveinput'):  # If true, this is the primary node
        with _print_on_err():
            print('=> Prepare target environments ...')
            for dist in OS_DISTS:
                name = '{0}_letstest'.format(dist)
                subprocess.check_output(
                    ['docker', 'build', '-f', '{0}.Dockerfile'.format(dist), '-t', name, '--network', 'host',
                     '--pull', '.'], cwd=BASE_ENV_PATH)
            print('=> Target environments ready.')
