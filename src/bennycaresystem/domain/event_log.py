class EventLog:

    def __init__(self, max_events=200):
        self.events = deque(maxlen=max_events)

    def record(self, event):
        self.events.appendleft((time.time(), event))