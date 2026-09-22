"""Interpretación de comandos en español."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from .github_client import GitHubClientError, PullRequestService


@dataclass(frozen=True)
class CommandResult:
    text: str
    should_exit: bool = False


class CommandProcessor:
    """Convierte frases del usuario en acciones concretas."""

    def __init__(self, prs: PullRequestService, speaker: Callable[[str], None] | None = None):
        self.prs = prs
        self.speaker = speaker or (lambda _message: None)

    def handle(self, raw_command: str) -> CommandResult:
        command = raw_command.strip()
        normalized = _normalize(command)
        if not normalized:
            return CommandResult("No escuché ningún comando.")

        if normalized in {"salir", "adios", "chau", "terminar", "cerrar asistente"}:
            return CommandResult("Nos vemos. Gracias por usar el asistente.", should_exit=True)
        if normalized in {"ayuda", "que podes hacer", "que puedes hacer"}:
            return CommandResult(self.help_text())

        try:
            result = self._handle_github_command(command, normalized)
            if result is not None:
                return CommandResult(result)
        except (GitHubClientError, ValueError) as exc:
            return CommandResult(str(exc))

        return self._handle_base_command(command, normalized)

    def help_text(self) -> str:
        return (
            "Puedo listar o contar PRs abiertos, cerrados, fusionados o todos; "
            "filtrarlos por autor; mostrar el detalle de un PR y sus revisiones. "
            "También sé decir la hora y el día, contar un chiste, abrir sitios y buscar información."
        )

    def _handle_github_command(self, command: str, normalized: str) -> str | None:
        author_match = re.search(r"(?:por|de)\s+@?([\w.-]+)\s*$", command, re.IGNORECASE)
        author = author_match.group(1) if author_match else None
        without_author = command[: author_match.start()].strip() if author_match else command
        normalized_without_author = _normalize(without_author)

        status = _extract_status(normalized_without_author)
        is_pr_command = bool(re.search(r"\bpr(?:s|s)?\b|pull requests?", normalized_without_author))
        if is_pr_command and re.search(r"\b(contar|cuantos|cuantas|cantidad)\b", normalized_without_author):
            count = self.prs.count_prs(status=status, author=author)
            suffix = f" del autor {author}" if author else ""
            return f"Hay {count} PRs {status}{suffix} en {self.prs.repository_name}."

        if is_pr_command and re.search(r"\b(listar|mostrar|ver|traer)\b", normalized_without_author):
            items = self.prs.list_prs(status=status, author=author)
            if not items:
                return f"No encontré PRs {status} en {self.prs.repository_name}."
            lines = [f"PRs {status} de {self.prs.repository_name}:"]
            lines.extend(f"#{item.number}: {item.title} — {item.author} ({item.url})" for item in items)
            return "\n".join(lines)

        detail_match = re.search(r"(?:detalle|detalles|ver)\s+(?:del\s+)?pr\s*#?\s*(\d+)", normalized)
        if detail_match:
            pull = self.prs.get_pr(int(detail_match.group(1)))
            state = "fusionado" if pull.merged_at is not None else pull.state
            author_name = getattr(getattr(pull, "user", None), "login", "desconocido")
            return (
                f"PR #{pull.number}: {pull.title}. Estado: {state}. Autor: {author_name}. "
                f"Rama {pull.head.ref} hacia {pull.base.ref}. Descripción: {pull.body or 'sin descripción'}. "
                f"Enlace: {pull.html_url}"
            )

        review_match = re.search(r"(?:revisiones|reviews|revisiones del pr)\s*(?:#|del pr\s*)?(\d+)", normalized)
        if review_match:
            reviews = self.prs.reviews(int(review_match.group(1)))
            if not reviews:
                return "Ese PR todavía no tiene revisiones."
            lines = [f"Revisiones del PR #{review_match.group(1)}:"]
            for review in reviews:
                reviewer = getattr(getattr(review, "user", None), "login", "desconocido")
                state = getattr(review, "state", "sin estado")
                body = getattr(review, "body", "") or "sin comentario"
                lines.append(f"{reviewer}: {state}. {body}")
            return "\n".join(lines)
        return None

    def _handle_base_command(self, command: str, normalized: str) -> CommandResult:
        if "que hora" in normalized:
            now = datetime.now().strftime("%H:%M")
            return CommandResult(f"En este momento son las {now}.")
        if "que dia" in normalized:
            days = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
            day = days[datetime.now().weekday()]
            return CommandResult(f"Hoy es {day}.")
        if "chiste" in normalized:
            try:
                import pyjokes

                return CommandResult(pyjokes.get_joke("es"))
            except Exception:
                return CommandResult("No pude conseguir un chiste en este momento.")
        if "abrir youtube" in normalized:
            return self._open_url("https://www.youtube.com", "YouTube")
        if "abrir navegador" in normalized:
            return self._open_url("https://www.google.com.ar", "el navegador")
        if normalized.startswith("busca en wikipedia"):
            return self._wikipedia(command[len("busca en wikipedia") :].strip())
        if normalized.startswith("busca en internet"):
            query = command[len("busca en internet") :].strip()
            try:
                import pywhatkit

                pywhatkit.search(query)
                return CommandResult(f"Busqué en internet: {query}.")
            except Exception:
                return CommandResult("No pude abrir la búsqueda en internet.")
        if normalized.startswith("reproducir"):
            query = command[len("reproducir") :].strip()
            try:
                import pywhatkit

                pywhatkit.playonyt(query)
                return CommandResult(f"Reproduciendo {query}.")
            except Exception:
                return CommandResult("No pude reproducir ese contenido.")
        if "precio de la accion" in normalized or "precio de accion" in normalized:
            return self._stock_price(command)
        return CommandResult("No reconocí el comando. Decí ayuda para ver ejemplos.")

    def _open_url(self, url: str, label: str) -> CommandResult:
        import webbrowser

        webbrowser.open(url)
        return CommandResult(f"Estoy abriendo {label}.")

    def _wikipedia(self, query: str) -> CommandResult:
        if not query:
            return CommandResult("Decime qué tema querés buscar en Wikipedia.")
        try:
            import wikipedia

            wikipedia.set_lang("es")
            return CommandResult(wikipedia.summary(query, sentences=1))
        except Exception:
            return CommandResult("No pude encontrar ese tema en Wikipedia.")

    def _stock_price(self, command: str) -> CommandResult:
        company = command.lower().split("de")[-1].strip()
        symbols = {"apple": "AAPL", "amazon": "AMZN", "google": "GOOGL", "tesla": "TSLA"}
        if company not in symbols:
            return CommandResult(f"No tengo configurada la acción de {company}.")
        try:
            import yfinance as yf

            price = yf.Ticker(symbols[company]).info["regularMarketPrice"]
            return CommandResult(f"La acción de {company} cotiza a {price} dólares.")
        except Exception:
            return CommandResult("No pude obtener el precio de esa acción.")


def _extract_status(command: str) -> str:
    if re.search(r"fusionad|mergead", command):
        return "fusionados"
    if re.search(r"cerrad", command):
        return "cerrados"
    if re.search(r"todos|todas", command):
        return "todos"
    return "abiertos"


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.lower())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")
