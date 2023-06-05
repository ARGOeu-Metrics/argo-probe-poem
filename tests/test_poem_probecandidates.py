import datetime
import unittest
from unittest import mock

import requests
from argo_probe_poem.poem_probecandidates import AnalyseProbeCandidates

mock_tenants = [
    {
        "name": "TENANT1",
        "schema_name": "tenant1",
        "domain_url": "tenant1.poem.devel.argo.grnet.gr",
        "created_on": "2022-09-24",
        "nr_metrics": 179,
        "nr_probes": 68,
        "combined": False
    },
    {
        "name": "TENANT2",
        "schema_name": "tenant2",
        "domain_url": "tenant2.poem.devel.argo.grnet.gr",
        "created_on": "2023-10-14",
        "nr_metrics": 24,
        "nr_probes": 14,
        "combined": False
    },
    {
        "name": "TENANT3",
        "schema_name": "tenant3",
        "domain_url": "poem-devel.tenant3.eu",
        "created_on": "2022-09-24",
        "nr_metrics": 47,
        "nr_probes": 24,
        "combined": False
    }
]

mock_candidates1 = []

mock_candidates2 = [
    {
        "name": "test-probe1",
        "status": "submitted",
        "created": "2023-06-05 11:06:34",
        "last_update": "2023-06-05 11:06:34"
    },
    {
        "name": "test-probe2",
        "status": "deployed",
        "created": "2023-05-22 08:34:35",
        "last_update": "2023-06-01 09:35:46"
    }
]

mock_candidates3 = [
    {
        "name": "test-probe3",
        "status": "testing",
        "created": "2023-06-01 11:06:34",
        "last_update": "2023-06-03 11:06:34"
    },
    {
        "name": "test-probe4",
        "status": "rejected",
        "created": "2023-05-22 08:34:35",
        "last_update": "2023-06-01 09:35:46"
    }
]

mock_candidates4 = [
    {
        "name": "test-probe5",
        "status": "processing",
        "created": "2023-06-01 11:06:34",
        "last_update": "2023-06-03 11:06:34"
    },
    {
        "name": "test-probe6",
        "status": "deployed",
        "created": "2023-05-22 08:34:35",
        "last_update": "2023-06-01 09:35:46"
    }
]

mock_candidates5 = [
    {
        "name": "test-probe7",
        "status": "deployed",
        "created": "2023-05-22 08:34:35",
        "last_update": "2023-06-01 09:35:46"
    },
    {
        "name": "test-probe8",
        "status": "rejected",
        "created": "2023-05-22 08:34:35",
        "last_update": "2023-06-01 09:35:46"
    }
]


class MockResponse:
    def __init__(self, data, status_code):
        self.data = data
        self.status_code = status_code

    def json(self):
        return self.data

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.exceptions.RequestException(
                "There has been an error"
            )


def mock_response1(*args, **kwargs):
    if args[0].endswith("tenants/"):
        return MockResponse(data=mock_tenants, status_code=200)

    else:
        return MockResponse(data=mock_candidates2, status_code=200)


def mock_response2(*args, **kwargs):
    if args[0].endswith("tenants/"):
        return MockResponse(data=mock_tenants, status_code=200)

    else:
        return MockResponse(data=mock_candidates3, status_code=200)


def mock_response3(*args, **kwargs):
    if args[0].endswith("tenants/"):
        return MockResponse(data=mock_tenants, status_code=200)

    else:
        return MockResponse(data=mock_candidates4, status_code=200)


def mock_response4(*args, **kwargs):
    if args[0].endswith("tenants/"):
        return MockResponse(data=mock_tenants, status_code=200)

    else:
        return MockResponse(data=mock_candidates1, status_code=200)


class AnalyseProbeCandidatesTests(unittest.TestCase):
    @mock.patch("argo_probe_poem.poem_probecandidates.get_now")
    @mock.patch("requests.get")
    def test_get_status_single_tenant_submitted(self, mock_get, mock_now):
        mock_now.return_value = datetime.datetime(2023, 6, 5, 12, 0, 13)
        mock_get.side_effect = mock_response1
        analysis = AnalyseProbeCandidates(
            hostname="mock.hostname.com",
            tokens=["TENANT1:m0ck_t0k3n"],
            timeout=30,
            warning_processing=1,
            warning_testing=2
        )
        self.assertEqual(
            analysis.get_status(), {
                "status": 2,
                "message": "New submitted probe: test-probe1"
            }
        )
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_has_calls([
            mock.call(
                "https://mock.hostname.com/api/v2/internal/public_tenants/",
                timeout=30
            ),
            mock.call(
                "https://tenant1.poem.devel.argo.grnet.gr/api/v2/probes/",
                headers={"x-api-key": "m0ck_t0k3n"},
                timeout=30
            )
        ], any_order=True)

    @mock.patch("argo_probe_poem.poem_probecandidates.get_now")
    @mock.patch("requests.get")
    def test_get_status_single_tenant_testing_no_warn(self, mock_get, mock_now):
        mock_now.return_value = datetime.datetime(2023, 6, 4, 12, 0, 13)
        mock_get.side_effect = mock_response2
        analysis = AnalyseProbeCandidates(
            hostname="mock.hostname.com",
            tokens=["TENANT1:m0ck_t0k3n"],
            timeout=30,
            warning_processing=1,
            warning_testing=3
        )
        self.assertEqual(
            analysis.get_status(), {
                "status": 0,
                "message": "No action required"
            }
        )
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_has_calls([
            mock.call(
                "https://mock.hostname.com/api/v2/internal/public_tenants/",
                timeout=30
            ),
            mock.call(
                "https://tenant1.poem.devel.argo.grnet.gr/api/v2/probes/",
                headers={"x-api-key": "m0ck_t0k3n"},
                timeout=30
            )
        ], any_order=True)

    @mock.patch("argo_probe_poem.poem_probecandidates.get_now")
    @mock.patch("requests.get")
    def test_get_status_single_tenant_testing_warn(self, mock_get, mock_now):
        mock_now.return_value = datetime.datetime(2023, 6, 5, 12, 0, 13)
        mock_get.side_effect = mock_response2
        analysis = AnalyseProbeCandidates(
            hostname="mock.hostname.com",
            tokens=["TENANT1:m0ck_t0k3n"],
            timeout=30,
            warning_processing=1,
            warning_testing=2
        )
        self.assertEqual(
            analysis.get_status(), {
                "status": 1,
                "message": "Probe 'test-probe3' has status 'testing' for 2 days"
            }
        )
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_has_calls([
            mock.call(
                "https://mock.hostname.com/api/v2/internal/public_tenants/",
                timeout=30
            ),
            mock.call(
                "https://tenant1.poem.devel.argo.grnet.gr/api/v2/probes/",
                headers={"x-api-key": "m0ck_t0k3n"},
                timeout=30
            )
        ], any_order=True)

    @mock.patch("argo_probe_poem.poem_probecandidates.get_now")
    @mock.patch("requests.get")
    def test_get_status_single_tenant_processing_no_warn(
            self, mock_get, mock_now
    ):
        mock_now.return_value = datetime.datetime(2023, 6, 3, 12, 0, 13)
        mock_get.side_effect = mock_response3
        analysis = AnalyseProbeCandidates(
            hostname="mock.hostname.com",
            tokens=["TENANT1:m0ck_t0k3n"],
            timeout=30,
            warning_processing=1,
            warning_testing=2
        )
        self.assertEqual(
            analysis.get_status(), {
                "status": 0,
                "message": "No action required"
            }
        )
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_has_calls([
            mock.call(
                "https://mock.hostname.com/api/v2/internal/public_tenants/",
                timeout=30
            ),
            mock.call(
                "https://tenant1.poem.devel.argo.grnet.gr/api/v2/probes/",
                headers={"x-api-key": "m0ck_t0k3n"},
                timeout=30
            )
        ], any_order=True)

    @mock.patch("argo_probe_poem.poem_probecandidates.get_now")
    @mock.patch("requests.get")
    def test_get_status_single_tenant_processing_with_warn(
            self, mock_get, mock_now
    ):
        mock_now.return_value = datetime.datetime(2023, 6, 4, 12, 0, 13)
        mock_get.side_effect = mock_response3
        analysis = AnalyseProbeCandidates(
            hostname="mock.hostname.com",
            tokens=["TENANT1:m0ck_t0k3n"],
            timeout=30,
            warning_processing=1,
            warning_testing=2
        )
        self.assertEqual(
            analysis.get_status(), {
                "status": 1,
                "message":
                    "Probe 'test-probe5' has status 'processing' for 1 day"
            }
        )
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_has_calls([
            mock.call(
                "https://mock.hostname.com/api/v2/internal/public_tenants/",
                timeout=30
            ),
            mock.call(
                "https://tenant1.poem.devel.argo.grnet.gr/api/v2/probes/",
                headers={"x-api-key": "m0ck_t0k3n"},
                timeout=30
            )
        ], any_order=True)

    @mock.patch("argo_probe_poem.poem_probecandidates.get_now")
    @mock.patch("requests.get")
    def test_get_status_single_tenant_no_candidates(self, mock_get, mock_now):
        mock_now.return_value = datetime.datetime(2023, 6, 4, 12, 0, 13)
        mock_get.side_effect = mock_response4
        analysis = AnalyseProbeCandidates(
            hostname="mock.hostname.com",
            tokens=["TENANT1:m0ck_t0k3n"],
            timeout=30,
            warning_processing=1,
            warning_testing=2
        )
        self.assertEqual(
            analysis.get_status(), {
                "status": 0,
                "message": "No action required"
            }
        )
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_has_calls([
            mock.call(
                "https://mock.hostname.com/api/v2/internal/public_tenants/",
                timeout=30
            ),
            mock.call(
                "https://tenant1.poem.devel.argo.grnet.gr/api/v2/probes/",
                headers={"x-api-key": "m0ck_t0k3n"},
                timeout=30
            )
        ], any_order=True)

