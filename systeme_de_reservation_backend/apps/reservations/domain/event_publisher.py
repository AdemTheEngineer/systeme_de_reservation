"""Interface abstraite de publication des Domain Events.

Python pur, aucune dépendance Django. Même logique que pour les
Repositories (`domain/repositories.py`) : l'implémentation concrète vit en
infrastructure (`infrastructure/event_publishers.py`) et dépend de cette
interface, jamais l'inverse — la couche application n'importe donc jamais
`infrastructure` directement, seulement cette abstraction.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from apps.core.domain.domain_event import DomainEvent


class EventPublisher(ABC):
    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Publie un Domain Event. À appeler après le commit de la transaction."""

    def publish_all(self, events: list[DomainEvent]) -> None:
        for event in events:
            self.publish(event)
