import argparse

import requests
from argo_probe_poem import utils
from argo_probe_poem.NagiosResponse import NagiosResponse
from argo_probe_poem.utils import errmsg_from_excp


def find_missing_metrics(arguments, tenant):
    metrics = requests.get('https://' + tenant['domain_url'] + utils.METRICS_API, timeout=arguments.timeout).json()

    missing_metrics = list(arguments.mandatory_metrics)
    for metric in metrics:
        if metric['name'] in arguments.mandatory_metrics:
            missing_metrics.remove(metric['name'])

    return missing_metrics



def utils_metric(arguments):
    nagios_response = NagiosResponse("All mandatory metrics are present!")

    try:
        tenants = requests.get('https://' + arguments.hostname + utils.TENANT_API, timeout=arguments.timeout).json()
        tenants = utils.remove_name_from_json(tenants, utils.SUPERPOEM)

        for tenant in tenants:
            # Check mandatory metrics
            try:
                missing_metrics = find_missing_metrics(arguments, tenant)

                for metric in missing_metrics:
                    nagios_response.setCode(NagiosResponse.CRITICAL)
                    nagios_response.writeCriticalMessage('Customer: ' + tenant['name'] + ' - Metric %s is missing!' % metric)

            except requests.exceptions.RequestException as e:
                nagios_response.setCode(NagiosResponse.CRITICAL)
                nagios_response.writeCriticalMessage('Customer: ' + tenant['name'] + ' - cannot connect to %s: %s' % ('https://' + tenant['domain_url'] + utils.METRICS_API,
                                                            errmsg_from_excp(e)))
            except ValueError as e:
                nagios_response.setCode(NagiosResponse.CRITICAL)
                nagios_response.writeCriticalMessage('Customer: ' + tenant['name'] + ' - %s - %s' % (utils.METRICS_API, errmsg_from_excp(e)))

            except Exception as e:
                nagios_response.setCode(NagiosResponse.CRITICAL)
                nagios_response.writeCriticalMessage('%s' % (errmsg_from_excp(e)))

    except requests.exceptions.RequestException as e:
        nagios_response.setCode(NagiosResponse.CRITICAL)
        nagios_response.writeCriticalMessage('cannot connect to %s: %s' % ('https://' + arguments.hostname + utils.TENANT_API,
                                                    errmsg_from_excp(e)))
    except ValueError as e:
        nagios_response.setCode(NagiosResponse.CRITICAL)
        nagios_response.writeCriticalMessage('%s - %s' % (utils.TENANT_API, errmsg_from_excp(e)))

    except Exception as e:
        nagios_response.setCode(NagiosResponse.CRITICAL)
        nagios_response.writeCriticalMessage('%s' % (errmsg_from_excp(e)))

    print(nagios_response.getMsg())
    raise SystemExit(nagios_response.getCode())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', dest='hostname', required=True, type=str, help='Super POEM FQDN')
    parser.add_argument('--mandatory-metrics', dest='mandatory_metrics', required=True,
     type=str, nargs='*', help='List of mandatory metrics seperated by space')
    parser.add_argument('-t', dest='timeout', type=int, default=180)
    arguments = parser.parse_args()

    utils_metric(arguments)
    

if __name__ == "__main__":
    main()
