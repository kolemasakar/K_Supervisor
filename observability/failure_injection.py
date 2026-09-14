class InjectedFailure(RuntimeError):
    pass


class DeterministicFailureInjector:
    def __init__(self, fail_on_calls=()):
        self.fail_on_calls = frozenset(int(item) for item in fail_on_calls)
        self.calls = 0

    def checkpoint(self, label: str = "failure injection") -> None:
        self.calls += 1
        if self.calls in self.fail_on_calls:
            raise InjectedFailure(f"{label} at call {self.calls}")
