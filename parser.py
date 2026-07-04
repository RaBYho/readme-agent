"""
parser.py
---------
Module responsable du scan du dossier local :
  1. Génération d'une arborescence textuelle (en ignorant les dossiers indésirables).
  2. Détection et lecture des fichiers "stratégiques" définis dans config.py.
  3. Assemblage du tout en un contexte texte unique, prêt à être envoyé au LLM.

Ce module ne connaît rien du LLM : il ne fait que produire une chaîne de
caractères décrivant le projet. Cela le rend testable indépendamment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from config import (
    IGNORED_DIRS,
    IGNORED_FILES,
    IGNORED_EXTENSIONS,
    STRATEGIC_FILES,
    MAX_FILE_SIZE_BYTES,
    MAX_CONTEXT_CHARS,
    MAX_TREE_DEPTH,
    LICENSE_FILENAMES,
    LICENSE_SIGNATURES,
    SOURCE_CODE_EXTENSIONS,
    MAX_SOURCE_FILES,
    MAX_SOURCE_FILE_SIZE_BYTES,
    MIN_SOURCE_FILE_SIZE_BYTES,
)


@dataclass
class LicenseInfo:
    """Représente la licence détectée dans le projet."""

    filename: str
    spdx_id: str
    display_name: str


@dataclass
class ProjectContext:
    """Représente le contexte extrait d'un projet, prêt à être formaté pour le LLM."""

    root_path: Path
    tree: str
    strategic_files: dict[str, str] = field(default_factory=dict)
    source_files: dict[str, str] = field(default_factory=dict)
    license_info: LicenseInfo | None = None

    def to_prompt_text(self) -> str:
        """
        Assemble l'arborescence, le contenu des fichiers stratégiques, des
        extraits de code source métier et les informations de licence en un
        unique bloc de texte, tronqué si nécessaire pour rester sous la
        limite MAX_CONTEXT_CHARS.
        """
        parts = [
            f"# Arborescence du projet : {self.root_path.name}",
            "```",
            self.tree,
            "```",
            "",
        ]

        if self.license_info:
            parts.append(
                f"# Licence détectée : {self.license_info.display_name} "
                f"(SPDX: {self.license_info.spdx_id}), fichier `{self.license_info.filename}`"
            )
        else:
            parts.append("# Licence détectée : aucune (pas de fichier LICENSE trouvé)")

        parts.append("")
        parts.append("# Contenu des fichiers stratégiques")

        for filename, content in self.strategic_files.items():
            parts.append(f"\n## Fichier : `{filename}`")
            parts.append("```")
            parts.append(content)
            parts.append("```")

        if self.source_files:
            parts.append("\n# Extraits de code source métier (pour ancrer les fonctionnalités décrites)")
            for filename, content in self.source_files.items():
                parts.append(f"\n## Fichier : `{filename}`")
                parts.append("```")
                parts.append(content)
                parts.append("```")

        full_text = "\n".join(parts)

        if len(full_text) > MAX_CONTEXT_CHARS:
            full_text = (
                full_text[:MAX_CONTEXT_CHARS]
                + "\n\n[... contexte tronqué car trop volumineux ...]"
            )

        return full_text


def _should_ignore_dir(dir_name: str) -> bool:
    """Détermine si un dossier doit être exclu du scan."""
    return dir_name in IGNORED_DIRS or dir_name.startswith(".") and dir_name not in {".env.example"}


def _should_ignore_file(file_name: str) -> bool:
    """Détermine si un fichier doit être exclu du scan (par nom ou extension)."""
    if file_name in IGNORED_FILES:
        return True
    extension = Path(file_name).suffix.lower()
    return extension in IGNORED_EXTENSIONS


def build_tree(root_path: Path, max_depth: int = MAX_TREE_DEPTH) -> str:
    """
    Construit une représentation textuelle de l'arborescence du projet,
    similaire à la commande `tree`, en excluant les dossiers/fichiers
    définis dans config.py.

    Args:
        root_path: Chemin racine du projet à scanner.
        max_depth: Profondeur maximale à explorer (évite les arborescences
                   gigantesques dans les gros repos).

    Returns:
        Une chaîne de caractères représentant l'arborescence.
    """
    lines: list[str] = [f"{root_path.name}/"]
    _walk_tree(root_path, prefix="", depth=0, max_depth=max_depth, lines=lines)
    return "\n".join(lines)


def _walk_tree(
    current_path: Path,
    prefix: str,
    depth: int,
    max_depth: int,
    lines: list[str],
) -> None:
    """Fonction récursive auxiliaire qui construit l'arborescence branche par branche."""
    if depth >= max_depth:
        return

    try:
        entries = sorted(
            current_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())
        )
    except PermissionError:
        return

    # Filtrage des entrées ignorées
    visible_entries = []
    for entry in entries:
        if entry.is_dir() and _should_ignore_dir(entry.name):
            continue
        if entry.is_file() and _should_ignore_file(entry.name):
            continue
        visible_entries.append(entry)

    for index, entry in enumerate(visible_entries):
        is_last = index == len(visible_entries) - 1
        connector = "└── " if is_last else "├── "
        suffix = "/" if entry.is_dir() else ""
        lines.append(f"{prefix}{connector}{entry.name}{suffix}")

        if entry.is_dir():
            extension = "    " if is_last else "│   "
            _walk_tree(entry, prefix + extension, depth + 1, max_depth, lines)


def find_strategic_files(root_path: Path) -> dict[str, str]:
    """
    Parcourt récursivement le projet à la recherche des fichiers stratégiques
    définis dans config.STRATEGIC_FILES, et lit leur contenu.

    Args:
        root_path: Chemin racine du projet.

    Returns:
        Un dictionnaire {chemin_relatif: contenu_du_fichier}.
    """
    found_files: dict[str, str] = {}

    for path in root_path.rglob("*"):
        if not path.is_file():
            continue

        # Ignore si un dossier parent est dans la liste d'exclusion
        if any(_should_ignore_dir(part) for part in path.relative_to(root_path).parts[:-1]):
            continue

        if path.name.lower() in STRATEGIC_FILES:
            relative_path = str(path.relative_to(root_path))
            found_files[relative_path] = _read_file_safely(path)

    return found_files


def _read_file_safely(path: Path) -> str:
    """
    Lit le contenu d'un fichier texte en le tronquant si besoin,
    et en gérant proprement les erreurs d'encodage.
    """
    try:
        size = path.stat().st_size
        content = path.read_text(encoding="utf-8", errors="replace")

        if size > MAX_FILE_SIZE_BYTES:
            content = content[:MAX_FILE_SIZE_BYTES] + "\n[... fichier tronqué ...]"

        return content
    except (OSError, UnicodeDecodeError) as error:
        return f"[Impossible de lire ce fichier : {error}]"


def find_source_code_files(
    root_path: Path,
    already_included: set[str],
) -> dict[str, str]:
    """
    Recherche des fichiers de code source "métier" (au-delà des simples points
    d'entrée déjà couverts par STRATEGIC_FILES) afin de donner au LLM des
    éléments concrets sur ce que fait réellement le projet, plutôt que de se
    limiter aux fichiers de configuration.

    Heuristique de sélection (volontairement simple et prévisible) :
      1. Exclut les dossiers ignorés (config.IGNORED_DIRS) et les fichiers déjà
         inclus comme fichiers stratégiques.
      2. Ne retient que les extensions de code source connues (config.SOURCE_CODE_EXTENSIONS).
      3. Ignore les fichiers trop petits (probablement du boilerplate/vide)
         et tronque les fichiers trop volumineux.
      4. Trie les candidats par taille décroissante (approximation simple de
         "quantité de logique contenue") et ne garde que les MAX_SOURCE_FILES
         premiers, pour borner la taille du contexte envoyé au LLM.

    Args:
        root_path: Chemin racine du projet.
        already_included: Ensemble des chemins relatifs déjà lus comme
            fichiers stratégiques, à ne pas dupliquer ici.

    Returns:
        Un dictionnaire {chemin_relatif: contenu_tronqué}, limité à MAX_SOURCE_FILES entrées.
    """
    candidates: list[tuple[Path, int]] = []

    for path in root_path.rglob("*"):
        if not path.is_file():
            continue

        relative_path = path.relative_to(root_path)

        if any(_should_ignore_dir(part) for part in relative_path.parts[:-1]):
            continue

        if str(relative_path) in already_included:
            continue

        if path.suffix.lower() not in SOURCE_CODE_EXTENSIONS:
            continue

        try:
            size = path.stat().st_size
        except OSError:
            continue

        if size < MIN_SOURCE_FILE_SIZE_BYTES:
            continue

        candidates.append((path, size))

    # Fichiers les plus "substantiels" en premier, dans la limite de MAX_SOURCE_FILES
    candidates.sort(key=lambda item: item[1], reverse=True)
    selected = candidates[:MAX_SOURCE_FILES]

    source_files: dict[str, str] = {}
    for path, _size in selected:
        relative_path = str(path.relative_to(root_path))
        content = _read_file_safely(path)
        if len(content) > MAX_SOURCE_FILE_SIZE_BYTES:
            content = content[:MAX_SOURCE_FILE_SIZE_BYTES] + "\n[... fichier tronqué ...]"
        source_files[relative_path] = content

    return source_files


def detect_license(root_path: Path) -> LicenseInfo | None:
    """
    Recherche un fichier de licence à la racine du projet (LICENSE, LICENSE.txt, etc.)
    et tente d'identifier son type via des motifs textuels connus (config.LICENSE_SIGNATURES).

    Cette détection est volontairement déterministe (pas de LLM) : elle ne doit
    jamais inventer une licence qui ne serait pas explicitement présente dans le fichier.

    Args:
        root_path: Chemin racine du projet.

    Returns:
        Une instance de LicenseInfo si un fichier de licence est trouvé, sinon None.
        Si le fichier existe mais qu'aucune signature connue ne correspond,
        le spdx_id retourné est "Unknown" avec le nom de fichier conservé.
    """
    for entry in root_path.iterdir():
        if not entry.is_file():
            continue
        if entry.name.lower() not in LICENSE_FILENAMES:
            continue

        content = _read_file_safely(entry).lower()

        for pattern, (spdx_id, display_name) in LICENSE_SIGNATURES:
            if pattern in content:
                return LicenseInfo(filename=entry.name, spdx_id=spdx_id, display_name=display_name)

        # Fichier de licence présent mais type non reconnu par nos signatures
        return LicenseInfo(filename=entry.name, spdx_id="Unknown", display_name="Licence non identifiée")

    return None


def parse_project(root_path: str | Path) -> ProjectContext:
    """
    Point d'entrée principal du module : scanne un projet local et retourne
    un ProjectContext prêt à être converti en texte pour le LLM.

    Args:
        root_path: Chemin (str ou Path) vers le dossier racine du projet.

    Returns:
        Une instance de ProjectContext.

    Raises:
        FileNotFoundError: si le chemin n'existe pas ou n'est pas un dossier.
    """
    root = Path(root_path).resolve()

    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Le dossier '{root}' n'existe pas ou n'est pas un dossier valide.")

    tree = build_tree(root)
    strategic_files = find_strategic_files(root)
    source_files = find_source_code_files(root, already_included=set(strategic_files.keys()))
    license_info = detect_license(root)

    return ProjectContext(
        root_path=root,
        tree=tree,
        strategic_files=strategic_files,
        source_files=source_files,
        license_info=license_info,
    )