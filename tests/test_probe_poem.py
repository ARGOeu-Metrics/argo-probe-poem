import copy
import unittest
from unittest.mock import patch, call, MagicMock

import requests
from argo_probe_poem.poem_cert import Certificate, \
    WarningCertificateException, CertificateException, SSLException
from argo_probe_poem.poem_metricapi import Metrics, MetricsException
from argo_probe_poem.utils import POEMException
from freezegun import freeze_time

mock_tenants = [
    {
        "name": "TENANT1",
        "schema_name": "tenant1",
        "domain_url": "tenant1.poem.devel.argo.grnet.gr",
        "created_on": "2022-09-24",
        "nr_metrics": 111,
        "nr_probes": 11
    },
    {
        "name": "TENANT2",
        "schema_name": "tenant2",
        "domain_url": "tenant2.poem.devel.argo.grnet.gr",
        "created_on": "2022-09-24",
        "nr_metrics": 222,
        "nr_probes": 22
    }
]

mock_metrics = [
    {
        "id": 329,
        "name": "argo.ams.publish-consume",
        "mtype": "Active",
        "tags": [
            "ams",
            "messaging",
            "argo"
        ],
        "probeversion": "ams-probe (present)",
        "group": "EGI",
        "description": "",
        "parent": "",
        "probeexecutable": "ams-probe",
        "config": [
            {
                "key": "maxCheckAttempts",
                "value": "3"
            },
            {
                "key": "timeout",
                "value": "60"
            },
            {
                "key": "path",
                "value": "/usr/libexec/argo/probes/ams"
            },
            {
                "key": "interval",
                "value": "30"
            },
            {
                "key": "retryInterval",
                "value": "5"
            }
        ],
        "attribute": [
            {
                "key": "ARGO_AMS_TOKEN",
                "value": "--token"
            },
            {
                "key": "ARGO_AMS_PROJECT",
                "value": "--project"
            }
        ],
        "dependancy": [],
        "flags": [],
        "files": [],
        "parameter": [],
        "fileparameter": []
    },
    {
        "id": 305,
        "name": "argo.poem-tools.check",
        "mtype": "Active",
        "tags": [
            "internal",
            "argo",
            "monitoring"
        ],
        "probeversion": "check_log (0.3.0)",
        "group": "EGI",
        "description": "Probe inspecting the execution of argo-poem-tools by "
                       "parsing the log file.",
        "parent": "",
        "probeexecutable": "check_log",
        "config": [
            {
                "key": "maxCheckAttempts",
                "value": "4"
            },
            {
                "key": "timeout",
                "value": "120"
            },
            {
                "key": "path",
                "value": "/usr/libexec/argo/probes/argo_tools"
            },
            {
                "key": "interval",
                "value": "120"
            },
            {
                "key": "retryInterval",
                "value": "120"
            }
        ],
        "attribute": [],
        "dependancy": [],
        "flags": [
            {
                "key": "NOHOSTNAME",
                "value": "1"
            },
            {
                "key": "NOPUBLISH",
                "value": "1"
            }
        ],
        "files": [],
        "parameter": [
            {
                "key": "--file",
                "value": "/var/log/argo-poem-tools/argo-poem-tools.log"
            },
            {
                "key": "--age",
                "value": "2"
            },
            {
                "key": "--app",
                "value": "argo-poem-packages"
            }
        ],
        "fileparameter": []
    },
    {
        "id": 323,
        "name": "generic.disk.usage-local",
        "mtype": "Active",
        "tags": [
            "internal",
            "disk"
        ],
        "probeversion": "check_disk (present)",
        "group": "EGI",
        "description": "",
        "parent": "",
        "probeexecutable": "check_disk",
        "config": [
            {
                "key": "maxCheckAttempts",
                "value": "3"
            },
            {
                "key": "timeout",
                "value": "15"
            },
            {
                "key": "path",
                "value": "$USER1$"
            },
            {
                "key": "interval",
                "value": "60"
            },
            {
                "key": "retryInterval",
                "value": "5"
            }
        ],
        "attribute": [],
        "dependancy": [],
        "flags": [
            {
                "key": "NOHOSTNAME",
                "value": "1"
            },
            {
                "key": "PNP",
                "value": "1"
            },
            {
                "key": "NOPUBLISH",
                "value": "1"
            }
        ],
        "files": [],
        "parameter": [
            {
                "key": "-w",
                "value": "10%"
            },
            {
                "key": "-c",
                "value": "5%"
            }
        ],
        "fileparameter": []
    },
    {
        "id": 293,
        "name": "generic.http.connect",
        "mtype": "Active",
        "tags": [
            "network",
            "http"
        ],
        "probeversion": "check_http (present)",
        "group": "EGI",
        "description": "This metric checks the HTTP service on the specified "
                       "host. It can test normal (http) and secure (https) "
                       "servers, follow redirects, search for strings and "
                       "regular expressions, check connection times, and "
                       "report on certificate expiration times.",
        "parent": "",
        "probeexecutable": "check_http",
        "config": [
            {
                "key": "interval",
                "value": "5"
            },
            {
                "key": "maxCheckAttempts",
                "value": "3"
            },
            {
                "key": "path",
                "value": "$USER1$"
            },
            {
                "key": "retryInterval",
                "value": "3"
            },
            {
                "key": "timeout",
                "value": "60"
            }
        ],
        "attribute": [
            {
                "key": "SSL",
                "value": "-S --sni"
            },
            {
                "key": "PORT",
                "value": "-p"
            },
            {
                "key": "PATH",
                "value": "-u"
            }
        ],
        "dependancy": [],
        "flags": [
            {
                "key": "OBSESS",
                "value": "1"
            },
            {
                "key": "PNP",
                "value": "1"
            }
        ],
        "files": [],
        "parameter": [
            {
                "key": "--link",
                "value": ""
            },
            {
                "key": "--onredirect",
                "value": "follow"
            }
        ],
        "fileparameter": []
    },
    {
        "id": 335,
        "name": "generic.certificate.validity",
        "mtype": "Active",
        "tags": [
            "certificate"
        ],
        "probeversion": "check_ssl_cert (2.80.0)",
        "group": "EGI",
        "description": "This metric verifies the SSL certificate on a web "
                       "server to make sure it is correctly installed, valid "
                       "and trusted.  It checks an X.509 certificate for the "
                       "following: \n- checks if the server is running and "
                       "delivers a valid certificate\n- checks if the CA "
                       "matches a given pattern\n- checks the validity",
        "parent": "",
        "probeexecutable": "check_ssl_cert",
        "config": [
            {
                "key": "timeout",
                "value": "240"
            },
            {
                "key": "retryInterval",
                "value": "30"
            },
            {
                "key": "path",
                "value": "$USER1$"
            },
            {
                "key": "maxCheckAttempts",
                "value": "2"
            },
            {
                "key": "interval",
                "value": "240"
            }
        ],
        "attribute": [
            {
                "key": "NAGIOS_HOST_CERT",
                "value": "-C"
            },
            {
                "key": "NAGIOS_HOST_KEY",
                "value": "-K"
            },
            {
                "key": "PORT",
                "value": "-p"
            }
        ],
        "dependancy": [],
        "flags": [],
        "files": [],
        "parameter": [
            {
                "key": "-w",
                "value": "14"
            },
            {
                "key": "-c",
                "value": "0"
            },
            {
                "key": "--rootcert-dir",
                "value": "/etc/grid-security/certificates"
            },
            {
                "key": "--rootcert-file",
                "value": "/etc/pki/tls/certs/ca-bundle.crt"
            },
            {
                "key": "--ignore-ocsp",
                "value": ""
            },
            {
                "key": "--ignore-sct",
                "value": ""
            }
        ],
        "fileparameter": []
    }
]


class MockResponse:
    def __init__(self, status_code, data=None):
        self.data = data
        self.status_code = status_code

        self.ok = False
        self.reason = "BAD REQUEST"
        if str(self.status_code).startswith("2"):
            self.ok = True
            self.reason = "OK"

        if self.status_code == 500:
            self.reason = "SERVER ERROR"

    def json(self):
        if self.data:
            return self.data

        else:
            raise requests.exceptions.RequestException("Requests exception")


def pass_web_api(*args, **kwargs):
    return MockResponse(
        data=mock_tenants,
        status_code=200
    )


def mock_function(*args, **kwargs):
    pass


def mock_expire_cert(*args, **kwargs):
    return [
        ("tenant1.poem.devel.argo.grnet.gr", b'20241212235959Z'),
        ("tenant2.poem.devel.argo.grnet.gr", b'20221212235959Z')
    ]


class PoemCertTests(unittest.TestCase):
    def setUp(self):
        self.cert = Certificate(
            hostname="poem.devel.argo.grnet.gr",
            cert="/etc/grid-security/hostcert.pem",
            key="/etc/grid-security/hostkey.pem",
            capath="/etc/grid-security/certificates/",
            skipped_tenants=[],
            timeout=60
        )
        self.cert_skipped_tenants = Certificate(
            hostname="poem.devel.argo.grnet.gr",
            cert="/etc/grid-security/hostcert.pem",
            key="/etc/grid-security/hostkey.pem",
            capath="/etc/grid-security/certificates/",
            skipped_tenants=["TENANT1"],
            timeout=60
        )

        self.mock_get_cert = MagicMock()
        mock_get_cert_instance = self.mock_get_cert.return_value
        mock_get_cert_instance.get_notAfter.return_value = b"20221212235959Z"
        mock_get_cert_instance.get_extension_count.return_value = 1
        mock_get_cert_instance.get_extension.return_value = MagicMock()
        mock_get_extension_instance = \
            mock_get_cert_instance.get_extension.return_value
        mock_get_extension_instance.get_short_name.return_value = \
            b"subjectAltName"
        mock_get_extension_instance.__str__.return_value = (
            "DNS:*.devel.argo.grnet.gr, DNS:*.argo.grnet.gr, "
            "DNS:*.multi.argo.grnet.gr, DNS:*.poem.argo.grnet.gr, "
            "DNS:*.poem.devel.argo.grnet.gr, DNS:*.ui.argo.grnet.gr, "
            "DNS:*.ui.devel.argo.grnet.gr, DNS:argo.grnet.gr, "
            "DNS:devel.argo.grnet.gr"
        )

    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_get_tenants(self, mock_get):
        mock_get.return_value = MockResponse(data=mock_tenants, status_code=200)
        tenants = self.cert._get_tenants()
        mock_get.assert_called_once_with(
            "https://poem.devel.argo.grnet.gr/api/v2/internal/public_tenants"
        )
        self.assertEqual(tenants, mock_tenants)

    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_get_tenants_with_skipped_tenants(self, mock_get):
        mock_get.return_value = MockResponse(data=mock_tenants, status_code=200)
        tenants = self.cert_skipped_tenants._get_tenants()
        mock_get.assert_called_once_with(
            "https://poem.devel.argo.grnet.gr/api/v2/internal/public_tenants"
        )
        self.assertEqual(tenants, [mock_tenants[1]])

    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_get_tenants_with_exception(self, mock_get):
        mock_get.return_value = MockResponse(
            data={"detail": "There has been a problem"}, status_code=400
        )
        with self.assertRaises(POEMException) as context:
            self.cert._get_tenants()
        mock_get.assert_called_once_with(
            "https://poem.devel.argo.grnet.gr/api/v2/internal/public_tenants"
        )
        self.assertEqual(
            context.exception.__str__(),
            "POEM: Tenant fetch error: 400 BAD REQUEST: There has been a "
            "problem"
        )

    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_get_tenants_with_exception_without_msg(self, mock_get):
        mock_get.return_value = MockResponse(status_code=500)
        with self.assertRaises(POEMException) as context:
            self.cert._get_tenants()
        mock_get.assert_called_once_with(
            "https://poem.devel.argo.grnet.gr/api/v2/internal/public_tenants"
        )
        self.assertEqual(
            context.exception.__str__(),
            "POEM: Tenant fetch error: Requests exception"
        )

    @freeze_time("1969-12-28")
    @patch("argo_probe_poem.poem_cert.Certificate.verify_client_cert")
    @patch("argo_probe_poem.poem_cert.Certificate._get_tenants")
    def test_all_passed(
            self, mock_get_tenants, mock_client_cert
    ):
        mock_get_tenants.return_value = mock_tenants
        mock_client_cert.side_effect = mock_function
        with patch(
                "argo_probe_poem.poem_cert.Certificate._get_certificate",
                self.mock_get_cert
        ):
            self.cert.verify()
        self.assertEqual(mock_client_cert.call_count, 2)
        mock_client_cert.assert_has_calls(
            [call(mock_tenants[0]), call(mock_tenants[1])], any_order=True
        )
        self.assertEqual(self.mock_get_cert.call_count, 2)
        self.mock_get_cert.assert_has_calls([
            call("tenant1.poem.devel.argo.grnet.gr"),
            call("tenant2.poem.devel.argo.grnet.gr")
        ], any_order=True)

    @freeze_time("2022-12-10")
    @patch("argo_probe_poem.poem_cert.Certificate.verify_client_cert")
    @patch("argo_probe_poem.poem_cert.Certificate._get_tenants")
    def test_certificate_expire_warning(
            self, mock_get_tenants, mock_client_cert
    ):
        mock_get_tenants.return_value = mock_tenants
        mock_client_cert.side_effect = mock_function
        with patch(
                "argo_probe_poem.poem_cert.Certificate._get_certificate",
                self.mock_get_cert
        ):
            with self.assertRaises(WarningCertificateException) as context:
                self.cert.verify()
        self.assertEqual(self.mock_get_cert.call_count, 2)
        self.mock_get_cert.assert_has_calls([
            call("tenant1.poem.devel.argo.grnet.gr"),
            call("tenant2.poem.devel.argo.grnet.gr")
        ], any_order=True)
        self.assertEqual(
            context.exception.__str__(),
            "TENANT1: Server certificate will expire in 2 days / "
            "TENANT2: Server certificate will expire in 2 days"
        )

    @freeze_time("1969-12-28")
    @patch("argo_probe_poem.poem_cert.Certificate.verify_client_cert")
    @patch("argo_probe_poem.poem_cert.Certificate._get_tenants")
    def test_certificate_wrong_cn(
            self, mock_get_tenants, mock_client_cert
    ):
        changed_mock_tenants = copy.deepcopy(mock_tenants)
        changed_mock_tenants[0]["domain_url"] = "test.example.com"
        mock_get_tenants.return_value = changed_mock_tenants
        mock_client_cert.side_effect = mock_function
        with patch(
                "argo_probe_poem.poem_cert.Certificate._get_certificate",
                self.mock_get_cert
        ):
            with self.assertRaises(CertificateException) as context:
                self.cert.verify()
        self.assertEqual(
            context.exception.__str__(),
            "TENANT1: Server certificate CN does not match test.example.com"
        )

    @patch("argo_probe_poem.poem_cert.Certificate._get_certificate")
    @patch("argo_probe_poem.poem_cert.Certificate.verify_client_cert")
    @patch("argo_probe_poem.poem_cert.Certificate._get_tenants")
    def test_raise_ssl_exception(
            self, mock_get_tenants, mock_client_cert, mock_servercert
    ):
        mock_get_tenants.return_value = mock_tenants
        mock_client_cert.side_effect = mock_function
        mock_servercert.side_effect = [
            SSLException("Connection timeout after 60 seconds"),
            SSLException('Server certificate verification failed: Not good')
        ]
        with self.assertRaises(CertificateException) as context:
            self.cert.verify()
        self.assertEqual(
            context.exception.__str__(),
            "TENANT1: Connection timeout after 60 seconds / "
            "TENANT2: Server certificate verification failed: Not good"
        )


class PoemMetricsTests(unittest.TestCase):
    def setUp(self):
        self.metrics = Metrics(
            hostname="poem.devel.argo.grnet.gr",
            mandatory_metrics=[
                "argo.poem-tools.check", "generic.disk.usage-local"
            ],
            skipped_tenants=[],
            timeout=180
        )

        self.metrics_missing = Metrics(
            hostname="poem.devel.argo.grnet.gr",
            mandatory_metrics=[
                "argo.poem-tools.check",
                "generic.disk.usage-local",
                "generic.procs.crond"
            ],
            skipped_tenants=[],
            timeout=180
        )

        self.metrics_skipped_tenants = Metrics(
            hostname="poem.devel.argo.grnet.gr",
            mandatory_metrics=[
                "argo.poem-tools.check",
                "generic.disk.usage-local"
            ],
            skipped_tenants=["TENANT1"],
            timeout=180
        )

    @patch("argo_probe_poem.poem_metricapi.requests.get")
    def test_get_tenants(self, mock_get):
        mock_get.return_value = MockResponse(data=mock_tenants, status_code=200)
        tenants = self.metrics._get_tenants()
        mock_get.assert_called_once_with(
            "https://poem.devel.argo.grnet.gr/api/v2/internal/public_tenants"
        )
        self.assertEqual(tenants, mock_tenants)

    @patch("argo_probe_poem.poem_metricapi.requests.get")
    def test_get_tenants_with_skipped_tenants(self, mock_get):
        mock_get.return_value = MockResponse(data=mock_tenants, status_code=200)
        tenants = self.metrics_skipped_tenants._get_tenants()
        mock_get.assert_called_once_with(
            "https://poem.devel.argo.grnet.gr/api/v2/internal/public_tenants"
        )
        self.assertEqual(tenants, [mock_tenants[1]])

    @patch("argo_probe_poem.poem_metricapi.requests.get")
    def test_get_tenants_with_exception(self, mock_get):
        mock_get.return_value = MockResponse(
            data={"detail": "There has been a problem"}, status_code=400
        )
        with self.assertRaises(POEMException) as context:
            self.metrics._get_tenants()
        mock_get.assert_called_once_with(
            "https://poem.devel.argo.grnet.gr/api/v2/internal/public_tenants"
        )
        self.assertEqual(
            context.exception.__str__(),
            "POEM: Tenant fetch error: 400 BAD REQUEST: There has been a "
            "problem"
        )

    @patch("argo_probe_poem.poem_metricapi.requests.get")
    def test_get_tenants_with_exception_without_msg(self, mock_get):
        mock_get.return_value = MockResponse(status_code=500)
        with self.assertRaises(POEMException) as context:
            self.metrics._get_tenants()
        mock_get.assert_called_once_with(
            "https://poem.devel.argo.grnet.gr/api/v2/internal/public_tenants"
        )
        self.assertEqual(
            context.exception.__str__(),
            "POEM: Tenant fetch error: Requests exception"
        )

    @patch("argo_probe_poem.poem_metricapi.requests.get")
    def test_get_metrics(self, mock_get):
        mock_get.return_value = MockResponse(data=mock_metrics, status_code=200)
        metrics = self.metrics._get_metrics(tenant=mock_tenants[0])
        mock_get.assert_called_once_with(
            "https://tenant1.poem.devel.argo.grnet.gr/api/v2/internal/"
            "public_metric", timeout=180
        )
        self.assertEqual(metrics, mock_metrics)

    @patch("argo_probe_poem.poem_metricapi.requests.get")
    def test_get_metrics_with_exception(self, mock_get):
        mock_get.return_value = MockResponse(
            data={"detail": "There has been a problem"}, status_code=400
        )
        with self.assertRaises(POEMException) as context:
            self.metrics._get_metrics(tenant=mock_tenants[0])
        mock_get.assert_called_once_with(
            "https://tenant1.poem.devel.argo.grnet.gr/api/v2/internal/"
            "public_metric", timeout=180
        )
        self.assertEqual(
            context.exception.__str__(),
            "POEM: Metrics fetch error: 400 BAD REQUEST: There has been a "
            "problem"
        )

    @patch("argo_probe_poem.poem_metricapi.requests.get")
    def test_get_metrics_with_exception_without_msg(self, mock_get):
        mock_get.return_value = MockResponse(status_code=500)
        with self.assertRaises(POEMException) as context:
            self.metrics._get_metrics(tenant=mock_tenants[0])
        mock_get.assert_called_once_with(
            "https://tenant1.poem.devel.argo.grnet.gr/api/v2/internal/"
            "public_metric", timeout=180
        )
        self.assertEqual(
            context.exception.__str__(),
            "POEM: Metrics fetch error: Requests exception"
        )

    @patch("argo_probe_poem.poem_metricapi.Metrics._get_metrics")
    @patch("argo_probe_poem.poem_metricapi.Metrics._get_tenants")
    def test_check_mandatory_metrics_ok(
            self, mock_get_tenants, mock_get_metrics
    ):
        mock_get_tenants.return_value = mock_tenants
        mock_get_metrics.return_value = mock_metrics
        self.metrics.check_mandatory()
        mock_get_tenants.assert_called_once()
        self.assertEqual(mock_get_metrics.call_count, 2)
        mock_get_metrics.assert_has_calls([
            call(mock_tenants[0]), call(mock_tenants[1]),
        ], any_order=True)

    @patch("argo_probe_poem.poem_metricapi.Metrics._get_metrics")
    @patch("argo_probe_poem.poem_metricapi.Metrics._get_tenants")
    def test_check_mandatory_metrics_missing(
            self, mock_get_tenants, mock_get_metrics
    ):
        mock_get_tenants.return_value = mock_tenants
        mock_get_metrics.return_value = mock_metrics
        with self.assertRaises(MetricsException) as context:
            self.metrics_missing.check_mandatory()
        mock_get_tenants.assert_called_once()
        self.assertEqual(mock_get_metrics.call_count, 2)
        mock_get_metrics.assert_has_calls([
            call(mock_tenants[0]), call(mock_tenants[1]),
        ], any_order=True)
        self.assertEqual(
            context.exception.__str__(),
            "TENANT1: Metric generic.procs.crond is missing / "
            "TENANT2: Metric generic.procs.crond is missing"
        )
