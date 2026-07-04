"""
badges.py
---------
Génère des badges Markdown (format shields.io) de manière déterministe,
à partir de ce qui a été réellement détecté dans le projet (licence,
fichiers stratégiques présents). Aucun badge n'est inventé : ce module
ne fait que traduire des faits déjà extraits par parser.py en Markdown.

Séparer cette logique du parsing et du prompt permet de faire évoluer le
rendu visuel des badges (style, couleurs) sans toucher au reste du pipeline.
"""

from __future__ import annotations

from urllib.parse import quote

from config import BADGE_STYLE, TECH_BADGE_RULES
from parser import ProjectContext


def _shields_url(label: str, message: str, color: str) -> str:
    """
    Construit une URL de badge shields.io au format "statique" :
    https://img.shields.io/badge/<label>-<message>-<color>

    Les espaces et caractères spéciaux sont encodés pour rester valides dans l'URL.
    """
    encoded_label = quote(label)
    encoded_message = quote(message)
    return f"https://img.shields.io/badge/{encoded_label}-{encoded_message}-{color}?style={BADGE_STYLE}"


def build_license_badge(project_context: ProjectContext) -> str | None:
    """
    Construit le badge Markdown de licence si une licence a été détectée.

    Returns:
        Une ligne Markdown `![License](...)` ou None si aucune licence n'est détectée
        ou si son type n'a pas pu être identifié.
    """
    license_info = project_context.license_info
    if license_info is None or license_info.spdx_id == "Unknown":
        return None

    url = _shields_url("license", license_info.spdx_id, "blue")
    return f"![License: {license_info.spdx_id}]({url})"


def build_tech_badges(project_context: ProjectContext) -> list[str]:
    """
    Construit les badges Markdown correspondant aux technologies détectées,
    en se basant uniquement sur la présence de fichiers stratégiques connus
    (voir config.TECH_BADGE_RULES). Ne déduit rien au-delà de ces règles explicites.

    Returns:
        Une liste de lignes Markdown de badges (peut être vide).
    """
    detected_filenames = {name.lower() for name in _basenames(project_context)}

    badges: list[str] = []
    for filename, (label, message, color) in TECH_BADGE_RULES.items():
        if filename in detected_filenames:
            url = _shields_url(label, message, color)
            badges.append(f"![{label}]({url})")

    return badges


def _basenames(project_context: ProjectContext) -> list[str]:
    """Extrait uniquement les noms de fichiers (sans le chemin relatif) des fichiers stratégiques trouvés."""
    return [key.split("/")[-1] for key in project_context.strategic_files.keys()]


def build_all_badges(project_context: ProjectContext) -> list[str]:
    """
    Point d'entrée principal : assemble tous les badges disponibles
    (technologies puis licence) pour un projet donné.

    Returns:
        Liste ordonnée de lignes Markdown de badges, prête à être insérée
        dans le contexte envoyé au LLM ou directement dans le README.
    """
    badges = build_tech_badges(project_context)

    license_badge = build_license_badge(project_context)
    if license_badge:
        badges.append(license_badge)

    return badges
