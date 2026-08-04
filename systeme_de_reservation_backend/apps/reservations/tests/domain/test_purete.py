"""Garde-fou architectural : les couches `domain/` (contexte réservations et
Shared Kernel) doivent rester en Python pur — aucun import Django ou DRF.

Le test analyse les imports par AST (pas de regex fragile) et échoue en
nommant le fichier et le module fautifs.
"""

import ast
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[3]  # → apps/
DOSSIERS_DOMAINE = [
    RACINE / 'reservations' / 'domain',
    RACINE / 'core' / 'domain',
    RACINE / 'paiements' / 'domain',
]
MODULES_INTERDITS = ('django', 'rest_framework')


def _modules_importes(fichier: Path):
    arbre = ast.parse(fichier.read_text(encoding='utf-8'))
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.Import):
            for alias in noeud.names:
                yield alias.name
        elif isinstance(noeud, ast.ImportFrom) and noeud.module and noeud.level == 0:
            yield noeud.module


@pytest.mark.parametrize('dossier', DOSSIERS_DOMAINE, ids=lambda d: str(d.relative_to(RACINE)))
def test_le_domaine_est_sans_dependance_django(dossier):
    assert dossier.is_dir(), f'{dossier} introuvable — structure DDD modifiée ?'
    violations = []
    for fichier in dossier.rglob('*.py'):
        for module in _modules_importes(fichier):
            if module.split('.')[0] in MODULES_INTERDITS:
                violations.append(f'{fichier.relative_to(RACINE)} importe {module}')
    assert violations == []
