from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'apps.core'

    def ready(self) -> None:
        """Composition root du câblage inter-contextes in-process.

        Seul endroit de l'application où un contexte (paiements) est
        explicitement relié à un autre (reservations) : les domaines eux-
        mêmes ne se connaissent pas, ils communiquent via les Domain Events
        et ce dispatcher (`apps.core.domain.dispatcher`).
        """
        from apps.core.domain.dispatcher import dispatcher
        from apps.paiements.domain.events import PaiementEchoue, PaiementValide
        from apps.reservations.application.dto import ConfirmerReservationInput, LibererCreneauInput
        from apps.reservations.application.use_cases.confirmer_reservation import ConfirmerReservationUseCase
        from apps.reservations.application.use_cases.liberer_creneau import LibererCreneauUseCase
        from apps.reservations.infrastructure.event_publishers import LoggingEventPublisher
        from apps.reservations.infrastructure.repositories import (
            DjangoCreneauSlotRepository,
            DjangoReservationRepository,
        )

        def _sur_paiement_valide(event: PaiementValide) -> None:
            use_case = ConfirmerReservationUseCase(DjangoReservationRepository(), LoggingEventPublisher())
            use_case.execute(
                ConfirmerReservationInput(reservation_id=event.reservation_id, paiement_id=event.paiement_id)
            )

        def _sur_paiement_echoue(event: PaiementEchoue) -> None:
            use_case = LibererCreneauUseCase(
                DjangoReservationRepository(), DjangoCreneauSlotRepository(), LoggingEventPublisher()
            )
            use_case.execute(LibererCreneauInput(reservation_id=event.reservation_id))

        dispatcher.register(PaiementValide, _sur_paiement_valide)
        dispatcher.register(PaiementEchoue, _sur_paiement_echoue)
