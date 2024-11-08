class ProbeResponse:
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3

    def __init__(self, msg=""):
        self._code = self.OK
        self._msg = msg

    def warning(self, msg):
        self._msg = f"WARNING - {msg}"

    def ok(self, msg):
        self._msg = f"OK - {msg}"
        self._code = self.OK

    def critical(self, msg):
        self._msg = f"CRITICAL - {msg}"
        self._code = self.CRITICAL

    def unknown(self, msg):
        self._msg = f"UNKNOWN - {msg}"
        self._code = self.UNKNOWN

    def code(self):
        return self._code

    def msg(self):
        return self._msg
