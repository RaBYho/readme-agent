"""
main.py
-------
Point d'entrée CLI de l'agent : orchestre le parsing du projet local
et la génération du README.md via OpenRouter.

Exemples d'utilisation :
    python main.py /chemin/vers/mon/projet
    python main.py . --model "meta-llama/llama-3.1-70b-instruct"
    python main.py . --output docs/README.md --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config import DEFAULT_MODEL, DEFAULT_OUTPUT_FILENAME, DEFAULT_README_LANGUAGE
from parser import parse_project
from badges import build_all_badges
from llm_client import OpenRouterClient, OpenRouterClientError

# Charge automatiquement un fichier .env local si python-dotenv est installé.
# Ceci est optionnel : l'agent fonctionne aussi si la variable d'environnement
# OPENROUTER_API_KEY est déjà exportée dans le shell.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def parse_args() -> argparse.Namespace:
    """Définit et parse les arguments de la ligne de commande."""
    parser_cli = argparse.ArgumentParser(
        description="Génère automatiquement un README.md pour un projet local via OpenRouter."
    )
    parser_cli.add_argument(
        "project_path",
        type=str,
        help="Chemin vers le dossier racine du projet à documenter.",
    )
    parser_cli.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Identifiant du modèle OpenRouter à utiliser (défaut : {DEFAULT_MODEL}).",
    )
    parser_cli.add_argument(
        "--output",
        type=str,
        default=None,
        help=(
            "Chemin de sortie du README généré. Par défaut : "
            f"'{DEFAULT_OUTPUT_FILENAME}' à la racine du projet analysé."
        ),
    )
    parser_cli.add_argument(
        "--lang",
        type=str,
        default=DEFAULT_README_LANGUAGE,
        help=f"Langue de rédaction du README (ex: 'English', 'Français'). Défaut : {DEFAULT_README_LANGUAGE}.",
    )
    parser_cli.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche le contexte extrait sans appeler le LLM (utile pour debug).",
    )

    return parser_cli.parse_args()


def run(project_path: str, model: str, output_path: str | None, lang: str, dry_run: bool) -> None:
    """
    Exécute le pipeline complet : parsing -> (optionnel) appel LLM -> écriture du fichier.

    Args:
        project_path: Chemin du projet à documenter.
        model: Modèle OpenRouter à utiliser.
        output_path: Chemin de sortie du README (ou None pour le défaut).
        lang: Langue de rédaction du README (ex: "English", "Français").
        dry_run: Si True, n'appelle pas le LLM et affiche uniquement le contexte.
    """
    print(f"🔍 Analyse du projet : {project_path}")

    try:
        project_context = parse_project(project_path)
    except FileNotFoundError as error:
        print(f"❌ Erreur : {error}", file=sys.stderr)
        sys.exit(1)

    context_text = project_context.to_prompt_text()
    badges = build_all_badges(project_context)

    print(f"📄 Contexte extrait : {len(context_text)} caractères, "
          f"{len(project_context.strategic_files)} fichier(s) stratégique(s), "
          f"{len(project_context.source_files)} fichier(s) de code source métier détecté(s).")

    if project_context.license_info:
        print(f"⚖️  Licence détectée : {project_context.license_info.display_name}")
    else:
        print("⚖️  Aucune licence détectée.")

    if badges:
        print(f"🏷️  Badges générés : {len(badges)}")

    if dry_run:
        print("\n--- CONTEXTE (dry-run, aucun appel LLM effectué) ---\n")
        print(context_text)
        if badges:
            print("\n--- BADGES GÉNÉRÉS ---\n")
            print(" ".join(badges))
        return

    print(f"🤖 Génération du README en {lang} via le modèle '{model}'...")

    try:
        client = OpenRouterClient(model=model)
        readme_content = client.generate_readme(context_text, badges=badges, language=lang)
    except OpenRouterClientError as error:
        print(f"❌ Erreur lors de l'appel à OpenRouter : {error}", file=sys.stderr)
        sys.exit(1)

    resolved_output = Path(output_path) if output_path else project_context.root_path / DEFAULT_OUTPUT_FILENAME
    resolved_output.write_text(readme_content, encoding="utf-8")

    print(f"✅ README.md généré avec succès : {resolved_output}")


def main() -> None:
    """Point d'entrée du script."""
    args = parse_args()
    run(
        project_path=args.project_path,
        model=args.model,
        output_path=args.output,
        lang=args.lang,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()