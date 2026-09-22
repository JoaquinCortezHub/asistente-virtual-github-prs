"""Punto de entrada: ``python -m asistente``."""

from __future__ import annotations

import argparse
import os

from .assistant import VirtualAssistant
from .commands import CommandProcessor
from .github_client import GitHubClientError, PullRequestService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Asistente virtual para consultar PRs de GitHub")
    parser.add_argument(
        "--repo",
        default=os.getenv("GITHUB_REPO"),
        help="Repositorio en formato owner/repo (también puede definirse con GITHUB_REPO)",
    )
    parser.add_argument("--modo", choices=("voz", "texto"), default="voz")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.repo:
        print("Falta indicar --repo owner/repo o definir GITHUB_REPO.")
        return 2
    try:
        service = PullRequestService(args.repo)
    except (GitHubClientError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1
    processor = CommandProcessor(service)
    VirtualAssistant(processor, mode=args.modo).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

