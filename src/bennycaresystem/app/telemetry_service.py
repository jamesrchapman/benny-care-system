class TelemetryService:

    def __init__(self):
        self.providers = {}

    def register(self, name, fn):
        self.providers[name] = fn

    def snapshot(self):

        snap = {}

        for name, fn in self.providers.items():

            try:
                snap[name] = fn()
            except Exception as e:
                snap[name] = {"error": str(e)}

        return snap