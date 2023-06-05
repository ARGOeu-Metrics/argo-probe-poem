import argparse
import datetime

import requests
from argo_probe_poem import utils


def get_now():
    return datetime.datetime.now()


class RequestException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


class AnalyseProbeCandidates:
    def __init__(
            self, hostname, tokens, timeout, warning_processing, warning_testing
    ):
        self.hostname = hostname
        self.timeout = timeout
        self.tokens = self._extract_tokens(tokens)
        self.warning_processing = warning_processing
        self.warning_testing = warning_testing

    @staticmethod
    def _extract_tokens(tokens):
        tokens_dict = dict()
        for token in tokens:
            [tenant, key] = token.split(":")
            tokens_dict.update({tenant: key})

        return tokens_dict

    def _fetch_tenants(self):
        try:
            response = requests.get(
                f"https://{self.hostname}{utils.TENANT_API}",
                timeout=self.timeout
            )

            response.raise_for_status()

            return response.json()

        except (
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
            requests.exceptions.RequestException
        ) as e:
            raise RequestException(
                f"{self.hostname}: Error fetching tenants: {str(e)}"
            )

    def _fetch_probe_candidates(self, tenant):
        try:
            response = requests.get(
                f"https://{tenant['domain_url']}/api/v2/probes/",
                headers={"x-api-key": self.tokens[tenant["name"]]},
                timeout=self.timeout
            )

            response.raise_for_status()

            return response.json()

        except (
                requests.exceptions.HTTPError,
                requests.exceptions.ConnectionError,
                requests.exceptions.RequestException
        ) as e:
            raise RequestException(
                f"{tenant.name}: Error fetching probe candidates: {str(e)}"
            )

    def _fetch_data(self):
        tenants = self._fetch_tenants()

        data = dict()

        for tenant in tenants:
            if tenant["name"] != utils.SUPERPOEM and \
                    tenant["name"] in self.tokens.keys():
                data.update({
                    tenant["name"]: self._fetch_probe_candidates(tenant)
                })

        return data

    def get_status(self):
        now = get_now()
        data = self._fetch_data()

        msg = "No action required"
        status = 0
        for tenant, candidates in data.items():
            for candidate in candidates:
                time_difference = now - datetime.datetime.strptime(
                    candidate["last_update"], "%Y-%m-%d %H:%M:%S"
                )
                if time_difference.days == 1:
                    plural = ""

                else:
                    plural = "s"

                if candidate["status"] == "submitted":
                    msg = f"New submitted probe: {candidate['name']}"
                    status = 2

                if candidate["status"] == "testing" and \
                        time_difference.days >= self.warning_testing:
                    msg = f"Probe '{candidate['name']}' has status 'testing' " \
                          f"for {time_difference.days} day{plural}"
                    status = 1

                if candidate["status"] == "processing" \
                        and time_difference.days >= self.warning_processing:
                    msg = f"Probe '{candidate['name']}' has status " \
                          f"'processing' for {time_difference.days} day{plural}"
                    status = 1

        return {
            "status": status,
            "message": msg
        }


def main():
    parser = argparse.ArgumentParser(
        "ARGO probe that parses POEM api for presence of probe candidates and "
        "checks their statuses"
    )
    parser.add_argument(
        "-H", "--hostname", dest="hostname", type=str, required=True,
        help="Name of the host"
    )
    parser.add_argument(
        "-t", "--timeout", dest="timeout", type=float, default=30,
        required=True, help="Seconds before connection times out (default: 30)"
    )
    parser.add_argument(
        "-k", "--token", dest="token", type=str, nargs="+", action="append",
        help="tenant token in form: <TENANT_NAME:token>"
    )
    parser.add_argument(
        "--warn-processing", dest="warning_processing", type=float, default=1,
        required=True,
        help="Days before probe returns warning if probe with status "
             "'processing' is present (default: 1)"
    )
    parser.add_argument(
        "--warn-testing", dest="warning_testing", type=float, default=3,
        required=True,
        help="Days before probe returns warning if probe with status 'testing' "
             "is present (default: 3)"
    )
    args = parser.parse_args()


if __name__ == "__main__":
    main()
