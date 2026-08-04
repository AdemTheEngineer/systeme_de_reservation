"""Publication des Domain Events — point d'extension vers le bus inter-services.

Hors périmètre de ce sprint (cf. section 8 du cahier des charges) : le bus
de messages réel (Kafka/RabbitMQ) qui déclenchera le service Paiement à la
réception de `ReservationCreee`, ou notifiera d'autres contextes à la
réception de `ReservationConfirmee`/`ReservationAnnulee`. En attendant,
cette implémentation se contente de logger l'événement.
"""

from __future__ import annotations

import logging

from apps.core.domain.domain_event import DomainEvent
from apps.reservations.domain.event_publisher import EventPublisher

logger = logging.getLogger('apps.reservations.events')


class LoggingEventPublisher(EventPublisher):
    """Implémentation par défaut : logge l'événement au lieu de le publier sur un bus réel."""

    def publish(self, event: DomainEvent) -> None:
        logger.info('Domain event published: %s', event)
        # TODO: brancher sur le bus de messages réel inter-services (Kafka/
        # RabbitMQ) pour déclencher le service Paiement (ReservationCreee)
        # et notifier les autres contextes (ReservationConfirmee/Annulee).
