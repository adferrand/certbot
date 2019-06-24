import datetime
import sys

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography import x509
from cryptography.x509 import ocsp
from six.moves import BaseHTTPServer

from certbot_integration_tests.utils.misc import GracefulTCPServer
from certbot_integration_tests.utils.constants import MOCK_OCSP_SERVER_PORT


def _create_ocsp_handler(cert_path, issuer_cert_path, issuer_key_path, ocsp_status_text):
    class ProxyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        def do_POST(self):
            with open(issuer_cert_path, 'rb') as file_h1:
                issuer_cert = x509.load_pem_x509_certificate(file_h1.read(), default_backend())
            with open(issuer_key_path, 'rb') as file_h2:
                issuer_key = serialization.load_pem_private_key(file_h2.read(), None, default_backend())
            with open(cert_path, 'rb') as file_h3:
                cert = x509.load_pem_x509_certificate(file_h3.read(), default_backend())

            ocsp_status = getattr(ocsp.OCSPCertStatus, ocsp_status_text)

            now = datetime.datetime.utcnow()
            revocation_time = now if ocsp_status == ocsp.OCSPCertStatus.REVOKED else None
            revocation_reason = x509.ReasonFlags.unspecified if ocsp_status == ocsp.OCSPCertStatus.REVOKED else None

            builder = ocsp.OCSPResponseBuilder()
            builder = builder.add_response(
                cert=cert, issuer=issuer_cert, algorithm=hashes.SHA1(),
                cert_status=ocsp_status,
                this_update=now,
                next_update=now + datetime.timedelta(hours=1),
                revocation_time=revocation_time, revocation_reason=revocation_reason
            ).responder_id(ocsp.OCSPResponderEncoding.NAME, issuer_cert)

            response = builder.sign(issuer_key, hashes.SHA256())

            self.send_response(200)
            self.end_headers()
            self.wfile.write(response.public_bytes(serialization.Encoding.DER))

    return ProxyHandler


if __name__ == '__main__':
    httpd = GracefulTCPServer(('', MOCK_OCSP_SERVER_PORT), _create_ocsp_handler(*sys.argv[1:5]))
    try:
        httpd.handle_request()
    except KeyboardInterrupt:
        pass
