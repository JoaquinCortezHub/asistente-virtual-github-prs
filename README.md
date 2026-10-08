# Asistente virtual para GitHub

Proyecto práctico de Ingeniería del Conocimiento. Es un asistente en Python, basado en el código entregado por la cátedra, que conserva funciones cotidianas y agrega consultas de solo lectura sobre pull requests de un repositorio de GitHub.

## Funciones

El asistente puede:

- listar o contar PRs abiertos, cerrados, fusionados o todos;
- filtrar PRs por autor;
- mostrar el detalle de un PR y sus ramas, autor, descripción y enlace;
- leer las revisiones de un PR;
- decir la hora y el día, contar un chiste, abrir YouTube o el navegador, buscar en Wikipedia o internet, reproducir un video y consultar precios de acciones.

Las consultas de GitHub se hacen con PyGithub. El token se toma de `GITHUB_TOKEN` o de la sesión local de `gh auth token`; nunca se guarda ni se imprime.

## Instalación

Se requiere Python 3.12 y `uv`.

```bash
uv sync
```

En Linux, el reconocimiento de voz necesita un micrófono y PyAudio. La salida de voz usa las voces instaladas y elige una voz en español cuando el sistema ofrece una.

Para repositorios privados, definí un token con permiso de lectura de Pull requests:

```bash
export GITHUB_TOKEN="tu-token-local"
```

También podés iniciar sesión con GitHub CLI:

```bash
gh auth login
```

No pegues tokens en el README, en el código ni en commits.

## Uso

Modo texto, recomendado para probar:

```bash
uv run python -m asistente --repo octocat/Hello-World --modo texto
```

Modo voz:

```bash
uv run python -m asistente --repo octocat/Hello-World --modo voz
```

En Omarchy, el motor TTS de Linux se instala desde una terminal con:

```bash
omarchy pkg add espeak-ng
```

Si el auricular aparece conectado pero se usa el micrófono interno, seleccioná el micrófono Bluetooth desde el panel de audio o ejecutá `wpctl status` para identificarlo. El programa usa la fuente de audio predeterminada de PipeWire.

También se puede usar `GITHUB_REPO=owner/repo` para no repetir `--repo`.

Ejemplos de comandos:

```text
listar PRs abiertos
contar PRs fusionados
listar PRs cerrados por octocat
detalle del PR #12
revisiones del PR #12
ayuda
adiós
```

## Pruebas

```bash
uv run pytest
```

Las pruebas usan objetos simulados para validar la interpretación de comandos, la clasificación de PRs y el manejo de revisiones sin depender de la red ni de un micrófono.

## Prueba de PR
Este pedazo de código no está en main.
