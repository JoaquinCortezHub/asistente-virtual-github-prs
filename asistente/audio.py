"""Entrada y salida de voz, cargadas de forma diferida."""

from __future__ import annotations

import os
from contextlib import contextmanager


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
        except ImportError as exc:
            print(f"[audio] Falta SpeechRecognition/PyAudio: {exc}")
            return ""

        try:
            recognizer = sr.Recognizer()
            with _silence_alsa_logs():
                microphone = sr.Microphone()
                with microphone as source:
                    print("Ya podés hablar...")
                    audio = recognizer.listen(source, timeout=10, phrase_time_limit=20)
            return recognizer.recognize_google(audio, language=self.language)
        except sr.WaitTimeoutError:
            print("[audio] No detecté voz dentro del tiempo de espera.")
        except sr.UnknownValueError:
            print("[audio] No pude entender lo que dijiste.")
        except sr.RequestError:
            print("[audio] El servicio de reconocimiento no está disponible.")
        except OSError as exc:
            print(f"[audio] No pude abrir el micrófono seleccionado: {exc}")
        except Exception as exc:
            message = str(exc).strip() or exc.__class__.__name__
            print(f"[audio] No pude procesar el audio: {message}")
            return ""
        return ""


@contextmanager
def _silence_alsa_logs():
    """Oculta el ruido de enumeración ALSA, sin ocultar errores de la app."""

    original_stderr = os.dup(2)
    null_fd = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(null_fd, 2)
        yield
    finally:
        os.dup2(original_stderr, 2)
        os.close(null_fd)
        os.close(original_stderr)
