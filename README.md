# argo-probe-poem

Package currently contains two tenant-aware probes checking POEM functionality. `poem-cert-probe` is checking if the tenants' certificates are valid, and `poem-metricapi-probe` is checking that all the tenants' POEMs contain required list of mandatory metrics.

## Synopsis

The probe checking the certificate has five arguments: 

```
# /usr/libexec/argo/probes/poem/poem-cert-probe --help
usage: poem-cert-probe [-h] -H HOSTNAME [--cert CERT] [--key KEY]
                       [--capath CAPATH] [-t TIMEOUT]

optional arguments:
  -h, --help       show this help message and exit
  -H HOSTNAME      hostname
  --cert CERT      Certificate
  --key KEY        Certificate key
  --capath CAPATH  CA directory
  -t TIMEOUT
```

Example execution of the probe:

```
# /usr/libexec/argo/probes/poem/poem-metricapi-probe -H "poem.argo.grnet.gr" -t 60 --cert /etc/nagios/globus/hostcert.pem --key /etc/nagios/globus/hostkey.pem --capath /etc/grid-security/certificates
OK - All certificates are valid!
```

The one checking the mandatory metrics' has only three: 

```
# /usr/libexec/argo/probes/poem/poem-metricapi-probe --help
usage: poem-metricapi-probe [-h] -H HOSTNAME --mandatory-metrics
                            [MANDATORY_METRICS [MANDATORY_METRICS ...]]
                            [-t TIMEOUT]

optional arguments:
  -h, --help            show this help message and exit
  -H HOSTNAME           Super POEM FQDN
  --mandatory-metrics [MANDATORY_METRICS [MANDATORY_METRICS ...]]
                        List of mandatory metrics seperated by space
  -t TIMEOUT
```

Example execution of the probe:

```
# /usr/libexec/argo/probes/poem/poem-metricapi-probe -H "poem.argo.grnet.gr" -t 60 --mandatory-metrics argo.AMSPublisher-Check org.nagios.AmsDirSize org.nagios.NagiosCmdFile org.nagios.ProcessCrond
OK - All mandatory metrics are present!
```
