import argparse
import datetime
import re
import socket
import sys

import requests
from OpenSSL import SSL
from argo_probe_poem import utils
from argo_probe_poem.probe_response import ProbeResponse

HOSTCERT = "/etc/grid-security/hostcert.pem"
HOSTKEY = "/etc/grid-security/hostkey.pem"
CAPATH = "/etc/grid-security/certificates/"


class CertificateException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


class WarningCertificateException(CertificateException):
    def __init__(self, msg):
        self.msg = msg


class SSLException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


class Certificate:
    def __init__(self, hostname, cert, key, capath, skipped_tenants, timeout):
        self.hostname = hostname
        self.cert = cert
        self.key = key
        self.capath = capath
        self.skipped_tenants = skipped_tenants
        self.timeout = timeout

    def _get_tenants(self):
        try:
            response = requests.get(
                f"https://{self.hostname}{utils.TENANT_API}"
            )

            if not response.ok:
                msg = (
                    f"Tenant fetch error: {response.status_code} "
                    f"{response.reason}"
                )

                try:
                    msg = f"{msg}: {response.json()['detail']}"

                except (ValueError, TypeError, KeyError):
                    pass

                raise utils.POEMException(msg)

            else:
                tenants = response.json()

                return([
                    item for item in tenants if (
                        item["name"] not in self.skipped_tenants and
                        item["name"] != utils.SUPERPOEM
                    )
                ])

        except requests.exceptions.RequestException as e:
            raise utils.POEMException(f"Tenant fetch error: {str(e)}")

    def verify_client_cert(self, tenant):
        try:
            requests.get(
                f"https://{tenant['domain_url']}",
                cert=(self.cert, self.key),
                verify=True
            )

        except requests.exceptions.RequestException as e:
            raise CertificateException(
                f"{tenant['name']}: Client certificate verification failed: "
                f"{str(e)}"
            )

        except Exception as e:
            raise CertificateException(f"{tenant['name']}: {str(e)}")

    def _get_certificate(self, hostname):
        try:
            context = SSL.Context(SSL.TLSv1_2_METHOD)
            context.load_verify_locations(None, self.capath)
            conn = SSL.Connection(
                context,
                socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            )
            conn.connect((hostname, 443))
            conn.set_tlsext_host_name(hostname.encode("utf-8"))
            conn.set_connect_state()
            conn.settimeout(self.timeout)
            conn.setblocking(1)
            conn.do_handshake()

            cert = conn.get_peer_certificate()

            conn.shutdown()
            conn.close()

            return cert

        except SSL.Error as e:
            raise SSLException(
                f"Server certificate verification failed: {str(e)}"
            )

        except socket.timeout as e:
            raise SSLException(
                f"Connection timeout after {self.timeout} seconds"
            )

        except socket.error as e:
            raise SSLException(f"Connection error: {str(e)}")

    @staticmethod
    def _is_cn_ok(alt_names, fqdn):
        alt_names = [item.strip()[4:] for item in alt_names.split(",")]
        cn_ok = False
        for cn in alt_names:
            pattern = re.compile(cn.replace('*', '[A-Za-z0-9_-]+?'))
            if bool(re.match(pattern, fqdn)):
                cn_ok = True
                break

        return cn_ok

    def verify_server_cert(self, tenant):
        try:
            fqdn = tenant["domain_url"]
            certificate = self._get_certificate(fqdn)

            not_after = datetime.datetime.strptime(
                certificate.get_notAfter().decode("utf-8"), "%Y%m%d%H%M%SZ"
            )
            today = datetime.datetime.now()

            if (not_after - today).days < 15:
                raise WarningCertificateException(
                    f"{tenant['name']}: Server certificate will expire in "
                    f"{(not_after - today).days} days"
                )

            subject_alt_name = ""
            for i in range(certificate.get_extension_count()):
                extension = certificate.get_extension(i)
                if extension.get_short_name().decode() == "subjectAltName":
                    subject_alt_name = str(extension)

            if not self._is_cn_ok(subject_alt_name, fqdn):
                raise CertificateException(
                    f"{tenant['name']}: Server certificate CN does not match "
                    f"{fqdn}"
                )

        except SSLException as e:
            raise CertificateException(f"{tenant['name']}: {str(e)}")

        except WarningCertificateException:
            raise

    def verify(self):
        tenants = self._get_tenants()

        critical = list()
        warning = list()
        for tenant in tenants:
            try:
                self.verify_client_cert(tenant)
                self.verify_server_cert(tenant)

            except WarningCertificateException as e:
                warning.append(str(e))
                continue

            except CertificateException as e:
                critical.append(str(e))
                continue

        if len(critical) > 0:
            raise CertificateException(" / ".join(critical))

        if len(warning) > 0:
            raise WarningCertificateException(" / ".join(warning))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-H", "--hostname", dest='hostname', required=True, type=str,
        help='hostname'
    )
    parser.add_argument(
        '--cert', dest='cert', default=HOSTCERT, type=str, help='Certificate'
    )
    parser.add_argument(
        '--key', dest='key', default=HOSTKEY, type=str, help='Certificate key'
    )
    parser.add_argument(
        '--capath', dest='capath', default=CAPATH, type=str, help='CA directory'
    )
    parser.add_argument(
        "--skipped-tenants", dest="skipped_tenants", type=str, nargs="*",
        help="space-separated list of tenants that are going to be skipped"
    )
    parser.add_argument('-t', "--timeout", dest='timeout', type=int, default=60)
    args = parser.parse_args()

    cert = Certificate(
        hostname=args.hostname,
        cert=args.cert,
        key=args.key,
        capath=args.capath,
        skipped_tenants=args.skipped_tenants,
        timeout=args.timeout
    )
    status = ProbeResponse()

    try:
        cert.verify()
        status.ok("All certificates are valid")

    except WarningCertificateException as e:
        status.warning(str(e))

    except CertificateException as e:
        status.critical(str(e))

    except Exception as e:
        status.unknown(str(e))

    print(status.msg())
    sys.exit(status.code())


if __name__ == "__main__":
    main()
