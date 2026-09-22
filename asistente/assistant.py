"""Bucle principal del asistente."""

from __future__ import annotations

from collections.abc import Callable

from .audio import MicrophoneListener, Speaker
from .commands import CommandProcessor


class VirtualAssistant:
    def __init__(
        self,
        processor: CommandProcessor,
        mode: str = "voz",
        listener: MicrophoneListener | None = None,
        speaker: Speaker | None = None,
        input_fn: Callable[[str], str] = input,
    ) -> None:
        self.processor = processor
        self.mode = mode
        self.listener = listener or MicrophoneListener()
        self.speaker = speaker or Speaker(enabled=mode == "voz")
        self.input_fn = input_fn

    def run(self) -> None:
        greeting = f"Asistente listo para consultar PRs de {self.processor.prs.repository_name}. Decí ayuda para ver comandos."
        self._respond(greeting)
        while True:
            try:
                command = self.input_fn("> ") if self.mode == "texto" else self.listener.listen()
            except (EOFError, KeyboardInterrupt):
                print()
                return
            if not command:
                continue
            result = self.processor.handle(command)
            self._respond(result.text)
            if result.should_exit:
                return

    def _respond(self, message: str) -> None:
        print(message)
        self.speaker.say(message.replace("\n", ". "))

