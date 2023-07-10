# argo-probe-poem

Package contains three tenant-aware probes checking POEM functionality.  is checking if the tenants' certificates are valid, `poem-metricapi-probe` is checking that all the tenants' POEMs contain required list of mandatory metrics. `poem-probecandidate-probe` is checking if there are any new probe candidates submitted to POEM, and raises issues based on its status and the days passed since the change of status.

## Synopsis

### `poem-cert-probe`

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

### `poem-metricapi-probe`

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

### `poem-probecandidate-probe`

The probe checking the presence of probe candidates has three mandatory and two optional arguments (with default values):

```
# /usr/libexec/argo/probes/poem/poem-probecandidate-probe -h
usage: ARGO probe that parses POEM api for presence of probe candidates and checks their statuses
       [-h] -H HOSTNAME -t TIMEOUT [-k TOKEN [TOKEN ...]]
       [--warn-processing WARNING_PROCESSING] [--warn-testing WARNING_TESTING]

optional arguments:
  -h, --help            show this help message and exit
  -H HOSTNAME, --hostname HOSTNAME
                        Name of the host
  -t TIMEOUT, --timeout TIMEOUT
                        Seconds before connection times out (default: 30)
  -k TOKEN [TOKEN ...], --token TOKEN [TOKEN ...]
                        tenant token in form: <TENANT_NAME:token>
  --warn-processing WARNING_PROCESSING
                        Days before probe returns warning if probe with status
                        'processing' is present (default: 1)
  --warn-testing WARNING_TESTING
                        Days before probe returns warning if probe with status
                        'testing' is present (default: 3)
```

Example execution of the probe:

```
# /usr/libexec/argo/probes/poem/poem-probecandidate-probe -H poem.argo.grnet.gr -t 60 --warn-processing 2 --warn-testing 3 -k <token>

OK - No action required
```
