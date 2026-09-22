"""Acceso de solo lectura a la API de GitHub."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import Any, Iterable

from github import Auth, Github
from github.GithubException import GithubException, UnknownObjectException


class GitHubClientError(RuntimeError):
    """Error legible para el usuario al consultar GitHub."""


def get_github_token() -> str | None:
    """Obtiene el token desde el entorno o desde la sesión local de gh.

    El token nunca se imprime ni se guarda en el repositorio.
    """

    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        return token

    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return None

    token = result.stdout.strip()
    return token or None


def build_github_client(token: str | None = None) -> Github:
    """Construye un cliente autenticado si hay una credencial disponible."""

    token = token if token is not None else get_github_token()
    if token:
        return Github(auth=Auth.Token(token))
    return Github()


@dataclass(frozen=True)
class PullRequestSummary:
    number: int
    title: str
    state: str
    author: str
    url: str
    merged: bool


class PullRequestService:
    """Consultas de PRs para un repositorio configurado."""

    def __init__(self, repository: str, github: Github | Any | None = None) -> None:
        if repository.count("/") != 1:
            raise ValueError("El repositorio debe tener el formato owner/repo.")
        owner, name = (part.strip() for part in repository.split("/", 1))
        if not owner or not name:
            raise ValueError("El repositorio debe tener el formato owner/repo.")
        self.repository_name = f"{owner}/{name}"
        self.github = github if github is not None else build_github_client()
        try:
            self.repository = self.github.get_repo(self.repository_name)
        except UnknownObjectException as exc:
            raise GitHubClientError(
                f"No encontré el repositorio {self.repository_name} o no tenés acceso."
            ) from exc
        except GithubException as exc:
            raise GitHubClientError(_github_error_message(exc)) from exc

    @staticmethod
    def _state_for(status: str) -> str:
        return "open" if status == "abiertos" else "all"

    def _pull_requests(self, status: str) -> Iterable[Any]:
        try:
            pulls = self.repository.get_pulls(
                state=self._state_for(status), sort="created", direction="desc"
            )
            for pull in pulls:
                if status == "abiertos" and pull.state != "open":
                    continue
                if status == "fusionados" and pull.merged_at is None:
                    continue
                if status == "cerrados" and pull.state != "closed":
                    continue
                yield pull
        except GithubException as exc:
            raise GitHubClientError(_github_error_message(exc)) from exc

    def list_prs(
        self, status: str = "abiertos", author: str | None = None, limit: int = 20
    ) -> list[PullRequestSummary]:
        if status not in {"abiertos", "cerrados", "fusionados", "todos"}:
            raise ValueError("Estado no válido.")
        author_normalized = author.casefold().lstrip("@").strip() if author else None
        result: list[PullRequestSummary] = []
        for pull in self._pull_requests(status):
            login = getattr(getattr(pull, "user", None), "login", "desconocido")
            if author_normalized and login.casefold() != author_normalized:
                continue
            result.append(
                PullRequestSummary(
                    number=pull.number,
                    title=pull.title,
                    state=pull.state,
                    author=login,
                    url=pull.html_url,
                    merged=pull.merged_at is not None,
                )
            )
            if len(result) >= limit:
                break
        return result

    def count_prs(self, status: str = "abiertos", author: str | None = None) -> int:
        return len(self.list_prs(status=status, author=author, limit=10_000))

    def get_pr(self, number: int) -> Any:
        try:
            return self.repository.get_pull(number)
        except UnknownObjectException as exc:
            raise GitHubClientError(f"No encontré el PR #{number} en este repositorio.") from exc
        except GithubException as exc:
            raise GitHubClientError(_github_error_message(exc)) from exc

    def reviews(self, number: int) -> list[Any]:
        pull = self.get_pr(number)
        try:
            return list(pull.get_reviews())
        except GithubException as exc:
            raise GitHubClientError(_github_error_message(exc)) from exc


def _github_error_message(exc: GithubException) -> str:
    if exc.status == 401:
        return "GitHub rechazó la autenticación. Revisá GITHUB_TOKEN o gh auth login."
    if exc.status == 403:
        return "GitHub rechazó la consulta o se alcanzó el límite de la API."
    if exc.status == 404:
        return "GitHub no encontró el recurso o tu cuenta no tiene acceso."
    return f"GitHub devolvió un error HTTP {exc.status}."
