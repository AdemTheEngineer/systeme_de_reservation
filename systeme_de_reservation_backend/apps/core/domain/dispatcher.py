"""Dispatcher d'événements de domaine in-process (Shared Kernel).

Python pur, aucune dépendance Django. Permet à un contexte borné d'émettre
un `DomainEvent` sans connaître qui le consomme ; le câblage effectif
(quel handler écoute quel événement) est fait par la composition root de
chaque app (`AppConfig.ready()`), jamais ici ni dans un domaine.

Conçu pour rester "swappable" vers un vrai broker plus tard : le contrat
(`register`/`dispatch`) ne change pas, seule l'implémentation de `dispatch`
changerait (publier sur Kafka/RabbitMQ au lieu d'appeler les handlers
synchrones enregistrés).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import TypeVar

from apps.core.domain.domain_event import DomainEvent

EventT = TypeVar('EventT', bound=DomainEvent)
Handler = Callable[[DomainEvent], None]


class EventDispatcher:
    def __init__(self) -> None:
        self._handlers: dict[type, list[Handler]] = defaultdict(list)

    def register(self, event_type: type[EventT], handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    def dispatch(self, event: DomainEvent) -> None:
        for handler in self._handlers[type(event)]:
            handler(event)

    def dispatch_all(self, events: list[DomainEvent]) -> None:
        for event in events:
            self.dispatch(event)


# Singleton partagé par toute l'application — le câblage (qui écoute quoi)
# est enregistré par chaque app dans son `AppConfig.ready()`.
dispatcher = EventDispatcher()
