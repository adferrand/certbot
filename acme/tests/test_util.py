"""Test utilities.

.. warning:: This module is not part of the public API.

"""
import os

from OpenSSL import crypto
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import josepy as jose
import pkg_resources


def load_vector(*names):
    """Load contents of a test vector."""
    # luckily, resource_string opens file in binary mode
    return pkg_resources.resource_string(
        __name__, os.path.join('testdata', *names))


def _guess_loader(filename, loader_pem, loader_der):
    _, ext = os.path.splitext(filename)
    if ext.lower() == '.pem':
        return loader_pem
    elif ext.lower() == '.der':
        return loader_der
    else:  # pragma: no cover
        raise ValueError("Loader could not be recognized based on extension")


def load_cert(*names):
    """Load certificate."""
    loader = _guess_loader(
        names[-1], crypto.FILETYPE_PEM, crypto.FILETYPE_ASN1)
    return crypto.load_certificate(loader, load_vector(*names))


def load_comparable_cert(*names):
    """Load ComparableX509 cert."""
    return jose.ComparableX509(load_cert(*names))


def load_csr(*names):
    """Load certificate request."""
    loader = _guess_loader(
        names[-1], crypto.FILETYPE_PEM, crypto.FILETYPE_ASN1)
    return crypto.load_certificate_request(loader, load_vector(*names))


def load_comparable_csr(*names):
    """Load ComparableX509 certificate request."""
    return jose.ComparableX509(load_csr(*names))


def load_rsa_private_key(*names):
    """Load RSA private key."""
    loader = _guess_loader(names[-1], serialization.load_pem_private_key,
                           serialization.load_der_private_key)
    return jose.ComparableRSAKey(loader(
        load_vector(*names), password=None, backend=default_backend()))


def load_pyopenssl_private_key(*names):
    """Load pyOpenSSL private key."""
    loader = _guess_loader(
        names[-1], crypto.FILETYPE_PEM, crypto.FILETYPE_ASN1)
    return crypto.load_privatekey(loader, load_vector(*names))
