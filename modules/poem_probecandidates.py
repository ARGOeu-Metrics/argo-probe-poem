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
                f"{tenant['name']}: Error fetching probe candidates: {str(e)}"
            )

    def _fetch_data(self):
        tenants = self._fetch_tenants()

        data = dict()

        for tenant in tenants:
            if tenant["name"] != utils.SUPERPOEM and \
                    tenant["name"] in self.tokens.keys():
                try:
                    data.update({
                        tenant["name"]: {
                            "data": self._fetch_probe_candidates(tenant)
                        }
                    })

                except RequestException as e:
                    data.update({
                        tenant["name"]: {
                            "exception": str(e)
                        }
                    })

        return data

    def get_status(self):
        now = get_now()

        try:
            data = self._fetch_data()

        except RequestException as e:
            return {
                "status": 2,
                "message": f"CRITICAL - {str(e)}"
            }

        else:
            msg = "No action required"
            warning_msg = []
            critical_msg = []
            tenants_handle = set()
            status = 0
            multi_tenant = len(data) > 1
            for tenant, candidates in data.items():
                if multi_tenant:
                    prefix = f"{tenant}: "

                else:
                    prefix = ""

                if "data" in candidates:
                    for candidate in candidates["data"]:
                        time_difference = now - datetime.datetime.strptime(
                            candidate["last_update"], "%Y-%m-%d %H:%M:%S"
                        )

                        time_difference = time_difference.days

                        if time_difference == 1:
                            plural = ""

                        else:
                            plural = "s"

                        if candidate["status"] == "submitted":
                            status = 2
                            if multi_tenant:
                                critical_msg.append(
                                    f"{prefix}New submitted probe: "
                                    f"'{candidate['name']}'"
                                )
                                tenants_handle.add(tenant)

                            else:
                                msg = f"New submitted probe: " \
                                      f"'{candidate['name']}'"

                        if candidate["status"] == "testing" and \
                                time_difference >= self.warning_testing:
                            if status == 0:
                                status = 1

                            warning_msg.append(
                                f"{prefix}Probe '{candidate['name']}' has "
                                f"status 'testing' for {time_difference} "
                                f"day{plural}"
                            )

                            if multi_tenant:
                                tenants_handle.add(tenant)

                        if candidate["status"] == "processing" \
                                and time_difference >= self.warning_processing:
                            if status == 0:
                                status = 1

                            warning_msg.append(
                                f"{prefix}Probe '{candidate['name']}' has "
                                f"status 'processing' for {time_difference} "
                                f"day{plural}"
                            )

                            if multi_tenant:
                                tenants_handle.add(tenant)

                else:
                    status = 2
                    critical_msg.append(data[tenant]["exception"])

                    if multi_tenant:
                        tenants_handle.add(tenant)

            if multi_tenant:
                if tenants_handle:
                    ext = ""
                    if len(tenants_handle) > 1:
                        ext = "s"
                    msg = f"Actions required for tenant{ext}: " \
                          f"{', '.join(sorted(list(tenants_handle)))}"

                if critical_msg:
                    joined_msgs = "\n".join(critical_msg)
                    msg = f"{msg}\n{joined_msgs}"

                if warning_msg:
                    joined_msgs = "\n".join(warning_msg)
                    msg = f"{msg}\n{joined_msgs}"

            else:
                if critical_msg:
                    msg = "\n".join(critical_msg)

                if warning_msg:
                    joined_msgs = "\n".join(warning_msg)
                    if status == 1:
                        msg = joined_msgs

                    else:
                        msg = f"{msg}\n{joined_msgs}"

            if status == 0:
                msg_prefix = "OK"

            elif status == 1:
                msg_prefix = "WARNING"

            elif status == 2:
                msg_prefix = "CRITICAL"

            else:
                msg_prefix = "UNKNOWN"

            return {
                "status": status,
                "message": f"{msg_prefix} - {msg}"
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
