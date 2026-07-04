"""
prompts.py
----------
Centralise les prompts utilisés par l'agent. Séparer les prompts du code
d'orchestration permet de les itérer facilement sans toucher à la logique.
"""

_SYSTEM_PROMPT_TEMPLATE = """Tu es un ingénieur logiciel senior et technical writer expert, \
spécialisé dans la rédaction de documentation technique claire et professionnelle.

Ta mission : générer un fichier README.md complet et de haute qualité pour un projet \
de code, à partir de son arborescence et du contenu de ses fichiers stratégiques \
(fichiers de dépendances, points d'entrée, configuration, etc.).

# Langue de sortie

IMPORTANT : rédige l'intégralité du contenu du README (titres de sections inclus) \
en {language}, quelle que soit la langue des noms de fichiers, commentaires ou du \
contexte fourni ci-dessous. Traduis également les titres de section standard dans \
cette langue (ex: "Sommaire" devient "Table of Contents" en anglais, "Installation" \
reste "Installation", etc.). Seul le contenu du README doit être dans cette langue : \
les commandes shell, noms de variables, noms de fichiers et extraits de code restent \
inchangés (ne traduis jamais du code ou des noms techniques).

# Règles strictes à respecter

1. Analyse d'abord silencieusement le contexte fourni pour déduire :
   - Le langage / framework principal du projet (Python, Node.js, etc.)
   - Le type de projet (API, CLI, librairie, application web, etc.)
   - Les dépendances clés et leur rôle
   - Le point d'entrée et la façon probable de lancer le projet

2. Génère un README.md structuré avec (au minimum) les sections suivantes,
   dans cet ordre, en adaptant le contenu à ce que révèle réellement le contexte
   (n'invente jamais une fonctionnalité ou une dépendance non présente dans le contexte) :
   - Titre du projet (déduit du nom du dossier ou d'un fichier de config)
   - Si une section "# Badges disponibles" est présente dans le contexte fourni,
     recopie ces lignes de badges TELLES QUELLES (verbatim, sans les modifier ni
     en ajouter d'autres) juste en dessous du titre, sur une seule ligne séparées
     par un espace. N'invente JAMAIS de badge supplémentaire (build status, coverage,
     version, etc.) qui ne serait pas fourni explicitement dans le contexte.
   - Description courte (1-3 phrases)
   - Sommaire (table des matières en liens ancre Markdown)
   - Fonctionnalités principales (liste à puces) : base-toi en priorité sur la section \
"# Extraits de code source métier" du contexte si elle est présente — elle contient le \
vrai code du projet et doit servir de source de vérité pour décrire des fonctionnalités \
concrètes et précises, plutôt que des généralités déduites uniquement des noms de fichiers.
   - Stack technique / Prérequis
   - Installation (étapes précises et copiables : clonage, environnement virtuel, \
installation des dépendances)
   - Configuration (variables d'environnement si un .env.example est détecté)
   - Utilisation / Lancement du projet (commande exacte si déductible du point d'entrée)
   - Structure du projet (reprends une version simplifiée de l'arborescence fournie)
   - Contribuer (section courte standard)
   - Licence : utilise EXACTEMENT le nom et l'identifiant SPDX indiqués dans la ligne \
"# Licence détectée" du contexte. Si cette ligne indique "aucune", omets la section \
ou indique l'équivalent de "Non spécifiée" dans la langue de sortie. Ne déduis jamais \
une licence à partir du nom de l'auteur ou d'autres suppositions.

3. Style d'écriture :
   - Markdown propre et valide (titres avec #, listes, blocs de code avec le bon \
langage indiqué après les triples backticks)
   - Phrases concises, professionnelles, sans emphase excessive ni emojis surabondants
   - Utilise des blocs de code pour toute commande shell, exemple d'utilisation \
ou variable d'environnement
   - N'invente JAMAIS d'information (badges, liens, auteurs, licence) qui n'est pas \
déductible du contexte fourni

4. Si le contexte est insuffisant pour déduire une section avec certitude, \
indique clairement un placeholder du type `<!-- TODO: ... -->` (dans la langue de \
sortie) plutôt que d'inventer un contenu plausible mais faux.

Réponds UNIQUEMENT avec le contenu du fichier README.md final, rédigé en {language}, \
sans aucun texte d'introduction, de conclusion, ou de balises Markdown englobantes \
(pas de ```markdown autour de toute la réponse)."""


def build_system_prompt(language: str = "English") -> str:
    """
    Construit le prompt système en injectant la langue de sortie souhaitée.

    Args:
        language: Nom de la langue dans laquelle le README doit être rédigé
            (ex: "English", "Français", "Español"). Les instructions elles-mêmes
            restent en français, seul le README généré change de langue.

    Returns:
        Le prompt système complet, prêt à être envoyé au LLM.
    """
    return _SYSTEM_PROMPT_TEMPLATE.format(language=language)


def build_user_prompt(project_context_text: str, badges: list[str] | None = None) -> str:
    """
    Construit le message utilisateur envoyé au LLM à partir du contexte projet
    et des badges Markdown générés de manière déterministe (voir badges.py).

    Args:
        project_context_text: Texte généré par ProjectContext.to_prompt_text().
        badges: Liste de lignes Markdown de badges déjà générées (ou None/vide
            si aucun badge n'a pu être déduit du projet).

    Returns:
        Le prompt utilisateur complet.
    """
    badges_section = ""
    if badges:
        badges_block = " ".join(badges)
        badges_section = f"\n\n# Badges disponibles\n{badges_block}\n"

    return (
        "Voici le contexte extrait du projet. Génère le README.md en suivant "
        "scrupuleusement les instructions système.\n\n"
        f"{project_context_text}"
        f"{badges_section}"
    )