"""
llm_client.py
-------------
Client d'accès à OpenRouter en utilisant le SDK officiel `openai`.
OpenRouter expose une API compatible avec celle d'OpenAI : il suffit de
changer le `base_url` et la clé d'API pour router les appels vers
n'importe quel modèle disponible sur https://openrouter.ai/models.

Ce module ne connaît rien du filesystem ni du parsing : il reçoit un texte
de contexte déjà préparé et retourne le texte généré par le modèle.
"""

from __future__ import annotations

import os

from openai import OpenAI, APIError, APIConnectionError, RateLimitError

from config import (
    OPENROUTER_BASE_URL,
    OPENROUTER_API_KEY_ENV_VAR,
    DEFAULT_MODEL,
    APP_REFERER_URL,
    APP_TITLE,
)
from prompts import build_system_prompt, build_user_prompt


class OpenRouterClientError(Exception):
    """Exception levée en cas d'échec de communication avec OpenRouter."""


class OpenRouterClient:
    """
    Encapsule la configuration et les appels à l'API OpenRouter.

    Exemple d'utilisation :
        client = OpenRouterClient()
        readme_content = client.generate_readme(project_context_text)
    """

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL) -> None:
        """
        Args:
            api_key: Clé API OpenRouter. Si None, elle est lue depuis la
                variable d'environnement OPENROUTER_API_KEY.
            model: Identifiant du modèle OpenRouter à utiliser
                (ex: "anthropic/claude-3.5-sonnet", "meta-llama/llama-3.1-70b-instruct").

        Raises:
            OpenRouterClientError: si aucune clé API n'est disponible.
        """
        resolved_api_key = api_key or os.getenv(OPENROUTER_API_KEY_ENV_VAR)

        if not resolved_api_key:
            raise OpenRouterClientError(
                f"Aucune clé API trouvée. Définis la variable d'environnement "
                f"'{OPENROUTER_API_KEY_ENV_VAR}' ou passe api_key explicitement."
            )

        self.model = model

        # Le SDK `openai` est utilisé tel quel : seul le base_url change.
        # Les headers "HTTP-Referer" et "X-Title" sont recommandés par OpenRouter
        # pour identifier ton application dans leur classement public.
        self.client = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=resolved_api_key,
            default_headers={
                "HTTP-Referer": APP_REFERER_URL,
                "X-Title": APP_TITLE,
            },
        )

    def generate_readme(
        self,
        project_context_text: str,
        badges: list[str] | None = None,
        language: str = "English",
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> str:
        """
        Envoie le contexte projet au LLM et retourne le README.md généré.

        Args:
            project_context_text: Texte du contexte projet (arborescence + fichiers).
            badges: Badges Markdown générés de manière déterministe (voir badges.py),
                insérés tels quels par le LLM sous le titre du README.
            language: Langue de rédaction du README (ex: "English", "Français").
            temperature: Température de génération (basse = plus déterministe,
                recommandé pour de la documentation technique).
            max_tokens: Nombre maximum de tokens dans la réponse.

        Returns:
            Le contenu Markdown du README généré.

        Raises:
            OpenRouterClientError: en cas d'échec de l'appel API.
        """
        system_prompt = build_system_prompt(language=language)
        user_prompt = build_user_prompt(project_context_text, badges=badges)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except RateLimitError as error:
            raise OpenRouterClientError(
                f"Limite de requêtes atteinte sur OpenRouter : {error}"
            ) from error
        except APIConnectionError as error:
            raise OpenRouterClientError(
                f"Impossible de se connecter à OpenRouter : {error}"
            ) from error
        except APIError as error:
            raise OpenRouterClientError(
                f"Erreur retournée par l'API OpenRouter : {error}"
            ) from error

        if not response.choices:
            raise OpenRouterClientError("La réponse du modèle ne contient aucun choix.")

        content = response.choices[0].message.content
        if not content:
            raise OpenRouterClientError("La réponse du modèle est vide.")

        return content.strip()