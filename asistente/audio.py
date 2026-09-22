"""Entrada y salida de voz, cargadas de forma diferida."""

from __future__ import annotations


class Speaker:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._engine = None

    def say(self, message: str) -> None:
        if not self.enabled:
            return
        try:
            import pyttsx3

            if self._engine is None:
                self._engine = pyttsx3.init()
                self._select_spanish_voice()
            self._engine.say(message)
            self._engine.runAndWait()
        except Exception as exc:
            print(f"[audio] No pude reproducir la respuesta hablada: {exc}")

    def _select_spanish_voice(self) -> None:
        if self._engine is None:
            return
        for voice in self._engine.getProperty("voices") or []:
            data = f"{getattr(voice, 'id', '')} {getattr(voice, 'name', '')}".lower()
            if any(language in data for language in ("spanish", "español", "es-es", "es_ar", "es-mx")):
                self._engine.setProperty("voice", voice.id)
                return


class MicrophoneListener:
    def __init__(self, language: str = "es-AR") -> None:
        self.language = language

    def listen(self) -> str:
        try:
            import speech_recognition as sr

            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                print("Ya podés hablar...")
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=20)
            return recognizer.recognize_google(audio, language=self.language)
        except Exception as exc:
            print(f"[audio] No pude entender el audio: {exc}")
            return ""

