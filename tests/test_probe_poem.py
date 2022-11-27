from types import SimpleNamespace
import unittest
from unittest.mock import patch
import requests
from freezegun import freeze_time

from argo_probe_poem.poem_cert import utils_func, NagiosResponse
from argo_probe_poem.poem_metricapi import utils_metric, NagiosResponse
import socket
from OpenSSL.SSL import Error as PyOpenSSLError


class MockResponse:
    def __init__(self, data, status_code):
        self.data = data
        self.status_code = status_code

    def json(self):
        return self.data

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.exceptions.RequestException("Error has occured")


def pass_web_api(*args, **kwargs):
    return MockResponse(
        data=mock_tenants,
        status_code=200
    )


mock_tenants = [
    {
        "name": "mock_name_1",
        "schema_name": "mock_1",
        "domain_url": "mock.domain.1",
        "created_on": "2022-09-24",
        "nr_metrics": 111,
        "nr_probes": 11
    },
    {
        "name": "mock_name_2",
        "schema_name": "mock_2",
        "domain_url": "mock.domain.2",
        "created_on": "2022-09-24",
        "nr_metrics": 222,
        "nr_probes": 22
    },
]


class ArgoProbePoemCert(unittest.TestCase):
    def setUp(self) -> None:
        arguments = {"hostname": "mock_hostname", "timeout": 60,
                     "cert": "mock_cert", "key": "mock_key", "capath": "mock_capath"}
        self.arguments = SimpleNamespace(**arguments)

    def tearDown(self) -> None:
        NagiosResponse._msgBagCritical = []

    @freeze_time("1969-12-28")
    @patch("builtins.print")
    @patch("argo_probe_poem.poem_cert.check_CN_matches_FQDN")
    @patch("argo_probe_poem.poem_cert.verify_servercert")
    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_all_passed(self, mock_requests, mock_servercert, mock_check_CN_matches_FQDN, mock_print):
        mock_requests.side_effect = pass_web_api
        mock_servercert.return_value = "foo_alt_names", b'20221212235959Z', True
        mock_check_CN_matches_FQDN.return_value = True

        with self.assertRaises(SystemExit) as e:
            utils_func(self.arguments)
        mock_print.assert_called_once_with("OK - All certificates are valid!")

        self.assertEqual(e.exception.code, 0)

    @freeze_time("2022-12-10")
    @patch("builtins.print")
    @patch("argo_probe_poem.poem_cert.check_CN_matches_FQDN")
    @patch("argo_probe_poem.poem_cert.verify_servercert")
    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_certificate_expire_warning(self, mock_requests, mock_servercert, mock_check_CN_matches_FQDN, mock_print):
        mock_requests.side_effect = pass_web_api
        mock_servercert.return_value = "foo_alt_names", b'20221212235959Z', True
        mock_check_CN_matches_FQDN.return_value = True

        with self.assertRaises(SystemExit) as e:
            utils_func(self.arguments)

        mock_print.assert_called_once_with(
            'WARNING - Customer: mock_name_1 - Server certificate will expire in 2 days / Customer: mock_name_2 - Server certificate will expire in 2 days')
        self.assertEqual(e.exception.code, 1)

    @patch("argo_probe_poem.poem_cert.verify_servercert")
    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_raise_socketerror(self, mock_requests, mock_verify_servcert):
        mock_requests.side_effect = pass_web_api
        mock_verify_servcert.side_effect = [
            socket.error('mocked socket error 1'),
            socket.error('mocked socket error 2')
        ]

        with self.assertRaises(SystemExit) as e:
            utils_func(self.arguments)

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_poem.poem_cert.verify_servercert")
    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_raise_sockettimeout(self, mock_requests, mock_verify_servcert):
        mock_requests.side_effect = pass_web_api
        mock_verify_servcert.side_effect = [
            socket.timeout('mocked socket timeout 1'),
            socket.timeout('mocked socket timeout 2')
        ]

        with self.assertRaises(SystemExit) as e:
            utils_func(self.arguments)

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_poem.poem_cert.verify_servercert")
    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_raise_sockettimeout(self, mock_requests, mock_servercert):
        mock_requests.side_effect = pass_web_api
        mock_servercert.side_effect = socket.timeout

        with self.assertRaises(SystemExit) as e:
            utils_func(self.arguments)

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_poem.poem_cert.client_cert_requests_get")
    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_raise_clientcert_requestexception(self, mock_requests_get, mock_client_cert_request):
        mock_requests_get.side_effect = pass_web_api
        mock_client_cert_request.side_effect = requests.exceptions.RequestException

        with self.assertRaises(SystemExit) as e:
            utils_func(self.arguments)

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_poem.poem_cert.client_cert_requests_get")
    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_raise_clientcert_exception(self, mock_requests_get, mock_client_cert_request):
        mock_requests_get.side_effect = pass_web_api
        mock_client_cert_request.side_effect = requests.exceptions.RequestException

        with self.assertRaises(SystemExit) as e:
            utils_func(self.arguments)

        self.assertEqual(e.exception.code, 2)

    @freeze_time("2022-11-11")
    @patch("argo_probe_poem.poem_cert.verify_servercert")
    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_raise_pyopensslerror_first_tenant_cert_failed(self, mock_requests, mock_servercert):
        mock_requests.side_effect = pass_web_api
        # first server failed
        mock_servercert.side_effect = [
            PyOpenSSLError('mocked PyOpenSSLError'),
            ('DNS:mock.domain.2', '20221127235959Z'.encode('utf-8'), False)
        ]

        with self.assertRaises(SystemExit) as e:
            utils_func(self.arguments)

        self.assertEqual(e.exception.code, 2)

    @freeze_time("2022-11-11")
    @patch("argo_probe_poem.poem_cert.verify_servercert")
    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_raise_pyopensslerror_second_tenant_cn_failed(self, mock_requests, mock_servercert):
        mock_requests.side_effect = pass_web_api
        # first server ok, second CN does not match
        alt_names = ('DNS:*.domain.1, DNS:*.domain.NO.2, DNS:mock.domain.1')
        mock_servercert.side_effect = [(alt_names, '20221127235959Z'.encode('utf-8'), True),
                                       (alt_names, '20221127235959Z'.encode('utf-8'), True)]

        with self.assertRaises(SystemExit) as e:
            utils_func(self.arguments)

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_poem.poem_cert.verify_servercert")
    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_raise_server_certificate_exception(self, mock_requests, mock_servercert):
        mock_requests.side_effect = pass_web_api
        mock_servercert.return_value = "foo_alt_names"

        with self.assertRaises(SystemExit) as e:
            utils_func(self.arguments)

        self.assertEqual(e.exception.code, 2)

    @patch("builtins.print")
    @patch("argo_probe_poem.poem_cert.requests.Response")
    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_raise_requestexception(self, mock_requests_get, mock_requests_resp, mock_print):
        mock_requests_get.return_value = mock_requests_resp
        mock_requests_resp.json.side_effect = requests.exceptions.RequestException

        with self.assertRaises(SystemExit) as e:
            utils_func(self.arguments)

        mock_print.assert_called_once_with(
            'CRITICAL - cannot connect to https://mock_hostname/api/v2/internal/public_tenants/: None')

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_raise_main_exception(self, mock_requests):
        mock_requests.side_effect = requests.exceptions.RequestException

        with self.assertRaises(SystemExit) as e:
            utils_func(self.arguments)

        self.assertEqual(e.exception.code, 2)

    @patch("builtins.print")
    @patch("argo_probe_poem.poem_cert.requests.Response")
    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_raise_value_error(self, mock_requests_get, mock_requests_resp, mock_print):
        mock_requests_get.return_value = mock_requests_resp
        mock_requests_resp.json.side_effect = ValueError

        with self.assertRaises(SystemExit) as e:
            utils_func(self.arguments)

        mock_print.assert_called_once_with(
            "CRITICAL - /api/v2/internal/public_tenants/ - None")

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_poem.poem_cert.check_CN_matches_FQDN")
    @patch("argo_probe_poem.poem_cert.verify_servercert")
    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_fail_cn_match_fqdn(self, mock_requests, mock_servercert, mock_check_CN_matches_FQDN):
        mock_requests.side_effect = pass_web_api
        mock_servercert.return_value = "foo_alt_names", b'20221212235959Z', True
        mock_check_CN_matches_FQDN.return_value = False

        with self.assertRaises(SystemExit) as e:
            utils_func(self.arguments)

        self.assertEqual(e.exception.code, 2)


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
    def test_all_passed(self, mock_requests, mock_find_missing_metrics, mock_print):
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
    def test_error_metric_missing(self, mock_requests, mock_find_missing_metrics, mock_print):
        mock_requests.side_effect = pass_web_api
        mock_find_missing_metrics.return_value = ["foo"]

        with self.assertRaises(SystemExit) as e:
            utils_metric(self.arguments)

        mock_print.assert_called_once_with(
            'CRITICAL - Customer: mock_name_1 - Metric foo is missing! / Customer: mock_name_2 - Metric foo is missing!')

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_poem.poem_metricapi.find_missing_metrics")
    @patch("argo_probe_poem.poem_metricapi.requests.get")
    def test_raise_mandatory_metrics_requestexception(self, mock_requests, mock_find_missing_metrics):
        mock_requests.side_effect = pass_web_api
        mock_find_missing_metrics.side_effect = requests.exceptions.RequestException

        with self.assertRaises(SystemExit) as e:
            utils_metric(self.arguments)

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_poem.poem_metricapi.find_missing_metrics")
    @patch("argo_probe_poem.poem_metricapi.requests.get")
    def test_raise_mandatory_metrics_value_exeption(self, mock_requests, mock_find_missing_metrics):
        mock_requests.side_effect = pass_web_api
        mock_find_missing_metrics.side_effect = ValueError

        with self.assertRaises(SystemExit) as e:
            utils_metric(self.arguments)

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_poem.poem_metricapi.find_missing_metrics")
    @patch("argo_probe_poem.poem_metricapi.requests.get")
    def test_raise_mandatory_metrics_exception(self, mock_requests, mock_find_missing_metrics):
        mock_requests.side_effect = pass_web_api
        mock_find_missing_metrics.return_value = ['missing_metric1', 'missing_metric2']

        with self.assertRaises(SystemExit) as e:
            utils_metric(self.arguments)

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_poem.poem_cert.requests.Response")
    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_raise_main_requestexception(self, mock_requests_get, mock_requests_resp):
        mock_requests_get.return_value = mock_requests_resp
        mock_requests_resp.json.side_effect = requests.exceptions.RequestException

        with self.assertRaises(SystemExit) as e:
            utils_metric(self.arguments)

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_poem.poem_cert.requests.Response")
    @patch("argo_probe_poem.poem_cert.requests.get")
    def test_raise_main_value_error(self, mock_requests_get, mock_requests_resp):
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


if __name__ == '__main__':
    unittest.main()
