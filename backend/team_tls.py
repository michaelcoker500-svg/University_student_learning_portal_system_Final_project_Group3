"""Create the private service identity and the public connection file for a team."""
import ipaddress
import json
import os
import ssl
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from .settings import CONFIG


def issue_bundle(directory, address, port):
    now = datetime.now(timezone.utc)
    issuer_key = ec.generate_private_key(ec.SECP256R1())
    service_key = ec.generate_private_key(ec.SECP256R1())
    issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "USLP team local CA")])
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, str(address))])

    def certificate(name, public_key, days, is_ca):
        return (
            x509.CertificateBuilder().subject_name(name).issuer_name(issuer)
            .public_key(public_key).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5)).not_valid_after(now + timedelta(days=days))
            .add_extension(x509.BasicConstraints(ca=is_ca, path_length=0 if is_ca else None), critical=True)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(public_key), critical=False)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(issuer_key.public_key()), critical=False)
            .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False,
                                         key_encipherment=False, data_encipherment=False, key_agreement=False,
                                         key_cert_sign=is_ca, crl_sign=is_ca, encipher_only=None,
                                         decipher_only=None), critical=True)
        )

    ca = certificate(issuer, issuer_key.public_key(), 366, True).sign(issuer_key, hashes.SHA256())
    server = (
        certificate(subject, service_key.public_key(), 365, False)
        .add_extension(x509.SubjectAlternativeName([x509.IPAddress(address)]), critical=False)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .sign(issuer_key, hashes.SHA256())
    )
    pem = serialization.Encoding.PEM
    (directory / "server.pem").write_bytes(server.public_bytes(pem))
    key_path = directory / "server.key"
    with os.fdopen(os.open(key_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "wb") as f:
        f.write(service_key.private_bytes(pem, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    profile = {"format": 1, "host": str(address), "port": port, "ca_pem": ca.public_bytes(pem).decode("ascii")}
    (directory / "portal-team.json").write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")


def server_identity(host, port):
    address = ipaddress.IPv4Address(host)
    if address.is_unspecified or address.is_multicast or address == ipaddress.IPv4Address("255.255.255.255"):
        raise ValueError("Choose the IPv4 address of the network adapter your teammates can reach.")
    if not 1 <= port <= 65535:
        raise ValueError("Choose an API port between 1 and 65535.")
    root = CONFIG.parent / "team-api"
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = root / f"{address}_{port}"
    if not target.exists():
        # Publish all three files at once. A concurrent launcher can reuse the winning bundle.
        with TemporaryDirectory(dir=root) as stage:
            bundle = Path(stage) / "bundle"
            bundle.mkdir(mode=0o700)
            issue_bundle(bundle, address, port)
            try:
                bundle.rename(target)
            except OSError:
                if not target.is_dir():
                    raise
    certificate = x509.load_pem_x509_certificate((target / "server.pem").read_bytes())
    if certificate.not_valid_after_utc <= datetime.now(timezone.utc):
        raise ValueError(f"Service certificate expired. Stop the API, rename {target} and start it again. "
                         "Give the new portal-team.json to each client.")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(target / "server.pem", target / "server.key")
    return context, target / "portal-team.json"
