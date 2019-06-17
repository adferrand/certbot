import subprocess
import os


def test_it():
    subprocess.check_call([
        'letsencrypt-auto',
         '-n',
         '--server', os.environ['DIRECTORY_URL'],
         '--no-verify-ssl',
         '--http-01-port', os.environ['HTTP_01_PORT'],
         '--manual-public-ip-loging-ok',
         '--non-interactive',
         '--agree-tos',
         '--register-unsafely-without-email',
         '--debug',
         '-vv',
         '--authenticator', 'standalone',
         '--installer', 'null',
         '-d', 'test.{0}'.format(os.environ['LE_SUFFIX'])
    ])
