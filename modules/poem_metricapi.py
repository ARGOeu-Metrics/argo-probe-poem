import argparse
import sys

import requests
from argo_probe_poem import utils
from argo_probe_poem.probe_response import ProbeResponse


class MetricsException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


class Metrics:
    def __init__(self, hostname, mandatory_metrics, skipped_tenants, timeout):
        self.hostname = hostname
        self.mandatory_metrics = set(mandatory_metrics)
        self.timeout = timeout
        if skipped_tenants:
            self.skipped_tenants = skipped_tenants
        else:
            self.skipped_tenants = []

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

    def _get_metrics(self, tenant):
        try:
            response = requests.get(
                f"https://{tenant['domain_url']}{utils.METRICS_API}",
                timeout=self.timeout
            )

            if not response.ok:
                msg = (
                    f"Metrics fetch error: {response.status_code} "
                    f"{response.reason}"
                )

                try:
                    msg = f"{msg}: {response.json()['detail']}"

                except (ValueError, TypeError, KeyError):
                    pass

                raise utils.POEMException(msg)

            else:
                metrics = response.json()

                return metrics

        except requests.exceptions.RequestException as e:
            raise utils.POEMException(f"Metrics fetch error: {str(e)}")

    def check_mandatory(self):
        tenants = self._get_tenants()

        msgs = list()
        for tenant in tenants:
            metrics = set([item["name"] for item in self._get_metrics(tenant)])

            if not self.mandatory_metrics.issubset(metrics):
                missing = self.mandatory_metrics.difference(metrics)

                if len(missing) > 1:
                    word = "Metrics"
                    verb = "are"

                else:
                    word = "Metric"
                    verb = "is"

                msgs.append(
                    f"{tenant['name']}: {word} {', '.join(missing)} {verb} "
                    f"missing"
                )

        if len(msgs) > 0:
            raise MetricsException(" / ".join(msgs))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-H', "--hostname", dest='hostname', required=True, type=str,
        help='SuperPOEM FQDN'
    )
    parser.add_argument(
        '--mandatory-metrics', dest='mandatory_metrics', required=True,
        type=str, nargs='*', help="space-separated list of mandatory metrics"
    )
    parser.add_argument(
        "--skipped-tenants", dest="skipped_tenants", type=str, nargs="*",
        help="space-separated list of tenants that are going to be skipped"
    )
    parser.add_argument(
        '-t', "--timeout", dest='timeout', type=int, default=180
    )
    args = parser.parse_args()

    status = ProbeResponse()

    metrics = Metrics(
        hostname=args.hostname,
        mandatory_metrics=args.mandatory_metrics,
        skipped_tenants=args.skipped_tenants,
        timeout=args.timeout
    )

    try:
        metrics.check_mandatory()
        status.ok("All mandatory metrics are present")

    except MetricsException as e:
        status.critical(str(e))

    except Exception as e:
        status.unknown(str(e))

    print(status.msg())
    sys.exit(status.code())


if __name__ == "__main__":
    main()
