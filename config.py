"""
config.py
---------
Configuration centralisée de l'agent : dossiers/fichiers à ignorer,
liste des fichiers "stratégiques" à lire pour donner du contexte au LLM,
et paramètres par défaut pour OpenRouter.

Garder toute la configuration ici évite les "magic strings" éparpillés
dans le reste du code et facilite l'ajustement du comportement de l'agent.
"""

from pathlib import Path

# --------------------------------------------------------------------------
# Dossiers à ignorer lors du scan (noms exacts, comparaison insensible à la casse)
# --------------------------------------------------------------------------
IGNORED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".idea",
    ".vscode",
    "dist",
    "build",
    ".next",
    ".pytest_cache",
    ".mypy_cache",
    "coverage",
    ".ruff_cache",
    "target",  # Rust/Java build dirs
    ".DS_Store",
}

# --------------------------------------------------------------------------
# Fichiers à ignorer explicitement (peu importe le dossier)
# --------------------------------------------------------------------------
IGNORED_FILES = {
    ".DS_Store",
    "poetry.lock",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
}

# --------------------------------------------------------------------------
# Extensions binaires à ne jamais tenter de lire comme du texte
# --------------------------------------------------------------------------
IGNORED_EXTENSIONS = {
    ".pyc", ".pyo", ".so", ".dll", ".exe", ".bin",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".rar",
    ".db", ".sqlite3",
    ".pdf",
}

# --------------------------------------------------------------------------
# Fichiers "stratégiques" : leur contenu est extrait en priorité car ils
# donnent un maximum d'information sur la nature et le fonctionnement du projet.
# La recherche se fait par nom de fichier exact (insensible à la casse).
# --------------------------------------------------------------------------
STRATEGIC_FILES = {
    # Points d'entrée
    "main.py", "app.py", "manage.py", "index.js", "index.ts", "server.js",
    # Dépendances Python
    "requirements.txt", "pyproject.toml", "setup.py", "pipfile",
    # Dépendances JS/TS
    "package.json", "tsconfig.json",
    # Conteneurisation / déploiement
    "dockerfile", "docker-compose.yml", "docker-compose.yaml",
    # Configuration diverse
    ".env.example", "makefile", "procfile",
}
# NOTE: "readme.md" est volontairement EXCLU de cette liste. L'inclure créerait
# une boucle de rétroaction : un README déjà présent (généré lors d'un run
# précédent) serait relu comme source de vérité et simplement reformulé,
# au lieu que l'agent analyse le vrai code à chaque exécution.

# --------------------------------------------------------------------------
# Détection du code source "métier" (au-delà des simples points d'entrée)
# --------------------------------------------------------------------------
# Extensions de fichiers considérées comme du code source pertinent à analyser
SOURCE_CODE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".vue", ".go", ".java", ".rb"}

# Nombre maximum de fichiers de code source additionnels inclus dans le contexte
# (au-delà des fichiers stratégiques déjà identifiés), pour ne pas faire
# exploser la taille du prompt envoyé au LLM.
MAX_SOURCE_FILES = 8

# Taille de troncature appliquée à chaque fichier de code source additionnel
# (plus petite que MAX_FILE_SIZE_BYTES car on peut en inclure plusieurs).
MAX_SOURCE_FILE_SIZE_BYTES = 15_000

# Taille minimale d'un fichier pour être considéré (évite les __init__.py vides
# ou les fichiers quasi vides qui n'apportent aucune information utile).
MIN_SOURCE_FILE_SIZE_BYTES = 80

# --------------------------------------------------------------------------
# Limites de sécurité pour éviter d'envoyer un contexte trop volumineux au LLM
# --------------------------------------------------------------------------
MAX_FILE_SIZE_BYTES = 50_000       # Un fichier stratégique au-delà de cette taille est tronqué
MAX_CONTEXT_CHARS = 60_000         # Taille max du contexte total envoyé au LLM
MAX_TREE_DEPTH = 6                 # Profondeur max de l'arborescence affichée

# --------------------------------------------------------------------------
# Configuration OpenRouter
# --------------------------------------------------------------------------
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY_ENV_VAR = "OPENROUTER_API_KEY"

DEFAULT_MODEL = "deepseek/deepseek-chat"

# Headers optionnels mais recommandés par OpenRouter pour le classement
# de ton app sur https://openrouter.ai/rankings
APP_REFERER_URL = "https://github.com/your-username/readme-agent"
APP_TITLE = "README Generator Agent"

DEFAULT_OUTPUT_FILENAME = "README.md"

# Langue par défaut dans laquelle le README est rédigé (modifiable via --lang en CLI)
DEFAULT_README_LANGUAGE = "English"

# --------------------------------------------------------------------------
# Détection de licence
# --------------------------------------------------------------------------
# Noms de fichiers de licence recherchés à la racine du projet (insensible à la casse)
LICENSE_FILENAMES = {
    "license", "license.txt", "license.md",
    "licence", "licence.txt", "licence.md",
    "copying",
}

# Signatures textuelles permettant d'identifier le type de licence à partir
# du contenu du fichier. Chaque entrée : (motif à chercher en minuscules) -> (SPDX ID, nom affiché).
# L'ordre importe : les motifs les plus spécifiques doivent être testés en premier
# (ex: "apache license, version 2.0" avant un test générique sur "apache").
LICENSE_SIGNATURES: list[tuple[str, tuple[str, str]]] = [
    ("gnu affero general public license", ("AGPL-3.0", "GNU Affero General Public License v3.0")),
    ("gnu general public license", ("GPL-3.0", "GNU General Public License v3.0")),
    ("gnu lesser general public license", ("LGPL-3.0", "GNU Lesser General Public License v3.0")),
    ("mozilla public license", ("MPL-2.0", "Mozilla Public License 2.0")),
    ("apache license, version 2.0", ("Apache-2.0", "Apache License 2.0")),
    ("apache license", ("Apache-2.0", "Apache License 2.0")),
    ("mit license", ("MIT", "MIT License")),
    ("the unlicense", ("Unlicense", "The Unlicense")),
    ("bsd 3-clause", ("BSD-3-Clause", "BSD 3-Clause License")),
    ("bsd 2-clause", ("BSD-2-Clause", "BSD 2-Clause License")),
    ("creative commons", ("CC", "Creative Commons License")),
    ("isc license", ("ISC", "ISC License")),
]

# --------------------------------------------------------------------------
# Badges (shields.io)
# --------------------------------------------------------------------------
BADGE_STYLE = "flat-square"  # style visuel des badges shields.io

# Association fichier stratégique détecté -> badge de langage/technologie.
# Chaque valeur est un tuple (label, message, couleur) au format shields.io.
TECH_BADGE_RULES: dict[str, tuple[str, str, str]] = {
    "package.json": ("node", "javascript", "339933"),
    "tsconfig.json": ("typescript", "typed", "3178C6"),
    "requirements.txt": ("python", "3.x", "3776AB"),
    "pyproject.toml": ("python", "3.x", "3776AB"),
    "setup.py": ("python", "3.x", "3776AB"),
    "dockerfile": ("docker", "containerized", "2496ED"),
}