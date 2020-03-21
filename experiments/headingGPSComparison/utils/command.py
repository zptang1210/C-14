class command:
    def __init__(self, timestamp, cmd, interStatus, rawParams):
        self.timestamp = timestamp
        self.cmd = cmd
        self.interStatus = interStatus
        self.rawParams = rawParams