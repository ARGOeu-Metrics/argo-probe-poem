import unittest
from types import SimpleNamespace
from unittest.mock import patch, call, MagicMock

import requests
from argo_probe_poem.poem_cert import Certificate, \
    WarningCertificateException, CertificateException, SSLException
from argo_probe_poem.poem_metricapi import utils_metric, NagiosResponse
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
        changed_mock_tenants = mock_tenants.copy()
        changed_mock_tenants[0]["domain_url"] = "test.example.com"
        mock_get_tenants.return_value = mock_tenants
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


class ArgoProbePoemMetrical(unittest.TestCase):
    def setUp(self) -> None:
        arguments = {"hostname": "mock_hostname",
                     "timeout": 60, "mandatory_metrics": "mock_metrics"}
        self.arguments = SimpleNamespace(**arguments)

    def tearDown(self) -> None:
        NagiosResponse._msgBagCritical = []

    @patch("builtins.print")
    @patch("argo_probe_poem.poem_metricapi.find_missing_metrics")
    @patch("argo_probe_poem.poem_metricapi.requests.get")
    def test_all_passed(
            self, mock_requests, mock_find_missing_metrics, mock_print
    ):
        mock_requests.side_effect = pass_web_api
        mock_find_missing_metrics.return_value = []

        with self.assertRaises(SystemExit) as e:
            utils_metric(self.arguments)

        mock_print.assert_called_once_with(
            'OK - All mandatory metrics are present!')

        self.assertEqual(e.exception.code, 0)

    @patch("builtins.print")
    @patch("argo_probe_poem.poem_metricapi.find_missing_metrics")
    @patch("argo_probe_poem.poem_metricapi.requests.get")
    def test_error_metric_missing(
            self, mock_requests, mock_find_missing_metrics, mock_print
    ):
        mock_requests.side_effect = pass_web_api
        mock_find_missing_metrics.return_value = ["foo"]

        with self.assertRaises(SystemExit) as e:
            utils_metric(self.arguments)

        mock_print.assert_called_once_with(
            'CRITICAL - Customer: TENANT1 - Metric foo is missing! '
            '/ Customer: TENANT2 - Metric foo is missing!')

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_poem.poem_metricapi.find_missing_metrics")
    @patch("argo_probe_poem.poem_metricapi.requests.get")
    def test_raise_mandatory_metrics_requestexception(
            self, mock_requests, mock_find_missing_metrics
    ):
        mock_requests.side_effect = pass_web_api
        mock_find_missing_metrics.side_effect = \
            requests.exceptions.RequestException

        with self.assertRaises(SystemExit) as e:
            utils_metric(self.arguments)

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_poem.poem_metricapi.find_missing_metrics")
    @patch("argo_probe_poem.poem_metricapi.requests.get")
    def test_raise_mandatory_metrics_value_exeption(
            self, mock_requests, mock_find_missing_metrics
    ):
        mock_requests.side_effect = pass_web_api
        mock_find_missing_metrics.side_effect = ValueError

        with self.assertRaises(SystemExit) as e:
            utils_metric(self.arguments)

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_poem.poem_metricapi.find_missing_metrics")
    @patch("argo_probe_poem.poem_metricapi.requests.get")
    def test_raise_mandatory_metrics_exception(
            self, mock_requests, mock_find_missing_metrics
    ):
        mock_requests.side_effect = pass_web_api
        mock_find_missing_metrics.return_value = [
            'missing_metric1', 'missing_metric2'
        ]

        with self.assertRaises(SystemExit) as e:
            utils_metric(self.arguments)

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_poem.poem_cert.requests.Response")
    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_raise_main_requestexception(
            self, mock_requests_get, mock_requests_resp
    ):
        mock_requests_get.return_value = mock_requests_resp
        mock_requests_resp.json.side_effect = \
            requests.exceptions.RequestException

        with self.assertRaises(SystemExit) as e:
            utils_metric(self.arguments)

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_poem.poem_cert.requests.Response")
    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_raise_main_value_error(
            self, mock_requests_get, mock_requests_resp
    ):
        mock_requests_get.return_value = mock_requests_resp
        mock_requests_resp.json.side_effect = ValueError

        with self.assertRaises(SystemExit) as e:
            utils_metric(self.arguments)

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_poem.poem_cert.requests.Response")
    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_raise_main_exception(self, mock_requests_get, mock_requests_resp):
        mock_requests_get.return_value = mock_requests_resp
        mock_requests_resp.json.side_effect = Exception

        with self.assertRaises(SystemExit) as e:
            utils_metric(self.arguments)

        self.assertEqual(e.exception.code, 2)
