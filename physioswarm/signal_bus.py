from __future__ import annotations

from collections import defaultdict

from .types import ControlSignal


class SignalBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[str]] = defaultdict(set)

    def subscribe(self, channel: str, subscriber_id: str) -> None:
        self._subscribers[channel].add(subscriber_id)

    def emit(self, signal: ControlSignal) -> list[str]:
        subscribers = sorted(self._subscribers.get(signal.channel, set()))
        if signal.target is not None:
            return [subscriber for subscriber in subscribers if subscriber == signal.target]
        return subscribers
