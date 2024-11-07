MIP_API = '/api/v2/metrics'
TENANT_API = '/api/v2/internal/public_tenants'
METRICS_API = '/api/v2/internal/public_metric'

SUPERPOEM = 'SuperPOEM Tenant'


class POEMException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return f"POEM: {str(self.msg)}"
