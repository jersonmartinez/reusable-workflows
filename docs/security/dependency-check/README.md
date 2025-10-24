🔁 Workflow reusable de Dependabot

Este repositorio incluye un workflow reusable que automatiza la gestión de Dependabot para cualquier repositorio consumidor. Puede operar en dos modos: programado (escribe/actualiza `.github/dependabot.yml`) o bajo demanda (solicita a Dependabot que procese un directorio ahora mismo).

Ubicación del reusable: `.github/workflows/dependabot.yml`

## Resumen rápido

- Modo programado: genera o actualiza `.github/dependabot.yml` añadiendo o sustituyendo únicamente la entrada correspondiente al par `package-ecosystem` + `directory`.
- Modo bajo demanda: elimina la entrada programada correspondiente (si existe) y llama a la API de Dependabot para pedir un escaneo inmediato.
- Idempotente y colaborativo: el workflow hace upsert (merge) de la entrada solicitada y evita subir cambios si la entrada ya existe y es idéntica.

## Cómo funciona (alto nivel)

1. El job recibe inputs: `package_ecosystem`, `directory`, `schedule_interval`, entre otros.
2. Si `schedule_interval` está vacío (cadena vacía):
   - El workflow entra en modo bajo demanda: elimina la entrada programada para ese `ecosistema+directorio` (si existe) y solicita a Dependabot un escaneo inmediato mediante `POST /repos/{owner}/{repo}/dependabot/updates`.
   - Si la llamada devuelve 404 (o hay errores de permisos), el paso añade un aviso en el summary pero no hace fallar todo el job.
3. Si `schedule_interval` está presente y es válido (`daily|weekly|monthly|quarterly|semiannually|yearly|cron`):
   - Se construye la entrada YAML deseada para ese par y se recupera el `.github/dependabot.yml` actual (si existe).
   - Se elimina la entrada previa para el mismo `ecosistema+directorio` y se añade la nueva entrada (merge/upsert).
   - Antes de escribir, se compara la entrada existente: si es idéntica, se omite la subida para ahorrar operaciones.
   - La escritura se realiza vía API (`PUT /repos/{owner}/{repo}/contents/.github/dependabot.yml`) con reintentos y reconciliación del `sha` para mitigar conflictos 409.

## Inputs (parámetros)

- `package_ecosystem` (string, requerido): ecosistema (npm, pip, maven, docker, github-actions, ...).
- `directory` (string, requerido): directorio en el repo donde está el manifiesto (p. ej. `/`, `/api`, `/app`).
- `dependency_file_path` (string, opcional): ruta exacta del manifiesto si quieres forzarla (por ejemplo `requirements.txt`, `Dockerfile`). Si se deja vacío el workflow intenta detectar el archivo según el ecosistema.
- `schedule_interval` (string, opcional): frecuencia de verificación (daily, weekly, monthly, quarterly, semiannually, yearly, cron). Cadena vacía => modo bajo demanda.
- `open_pull_requests_limit` (number, opcional): límite de PRs abiertos (por defecto 10).
- `auto_approve` (boolean, opcional): si `true`, el job de auto-approve se habilita para aprobar PRs de Dependabot.
- `auto_merge` (boolean, opcional): si `true`, habilita el job que intenta auto-fusionar PRs.
- `auto_merge_label` (string): etiqueta requerida para filtrar PRs a auto-merge (por defecto `dependencies`).
- `allow_major_versions` (boolean): si `false`, añade una regla `ignore` para `version-update:semver-major`.

## Ejemplos de uso

1) Programado (añade/actualiza la entrada en `.github/dependabot.yml`):

```yaml
jobs:
  dependabot-api:
    uses: jersonmartinez/reusable-workflows/.github/workflows/dependabot.yml@main
    with:
      package_ecosystem: "pip"
      directory: "/api"
      schedule_interval: "weekly"
      open_pull_requests_limit: 10
      allow_major_versions: false
```

2) Bajo demanda (no escribe `.github/dependabot.yml`, solicita escaneo inmediato):

```yaml
jobs:
  dependabot-api-on-demand:
    uses: jersonmartinez/reusable-workflows/.github/workflows/dependabot.yml@main
    with:
      package_ecosystem: "pip"
      directory: "/api"
      schedule_interval: ''   # cadena vacía -> modo bajo demanda
      open_pull_requests_limit: 10
```

3) Pipeline con varios jobs (una invocación por directorio/ecosistema):

```yaml
jobs:
  dependabot-api:
    uses: jersonmartinez/reusable-workflows/.github/workflows/dependabot.yml@main
    with:
      package_ecosystem: "pip"
      directory: "/api"
      schedule_interval: "weekly"

  dependabot-app:
    uses: jersonmartinez/reusable-workflows/.github/workflows/dependabot.yml@main
    with:
      package_ecosystem: "pip"
      directory: "/app"
      schedule_interval: "weekly"

  dependabot-docker:
    uses: jersonmartinez/reusable-workflows/.github/workflows/dependabot.yml@main
    with:
      package_ecosystem: "docker"
      directory: "/"
      schedule_interval: "weekly"

  dependabot-actions:
    uses: jersonmartinez/reusable-workflows/.github/workflows/dependabot.yml@main
    with:
      package_ecosystem: "github-actions"
      directory: "/"
      schedule_interval: "weekly"
```

> En modo programado, varias invocaciones consolidarán todas las entradas en un solo `.github/dependabot.yml` (idempotente).

## Requisitos y permisos

- Token: `GITHUB_TOKEN` con permisos mínimos recomendados:

```yaml
permissions:
  contents: write
  pull-requests: write
  security-events: write
```

- Runner: `ubuntu-latest` (o cualquier runner que incluya `gh` CLI). El reusable usa `gh api` para interactuar con la API de contenidos y el endpoint de Dependabot.
- Herramientas en runner:
  - `gh` (GitHub CLI) — requerido.
  - `base64` — para codificar contenido antes de subirlo.
  - `jq` — opcional, usado para parseo de JSON en operaciones de merge; si no está disponible, el workflow degrada operaciones y lo comunica en el summary.

## Comportamiento detallado y garantías

- Upsert (merge): el workflow elimina la entrada previa para el mismo `package_ecosystem`+`directory` y añade la nueva, preservando el resto de entradas en `.github/dependabot.yml`.
- Evitar escrituras innecesarias: si la entrada objetivo ya existe y es idéntica, la operación de PUT se omite.
- Manejo de concurrencia: las escrituras usan reintentos y reconciliación del `sha` (evita/fija 409 Conflict cuando otro proceso actualiza el fichero al mismo tiempo).
- Modo bajo demanda: elimina la entrada programada y llama a `POST /repos/{owner}/{repo}/dependabot/updates`. Si la API devuelve 404 o hay errores de permisos, el job no falla entero: se registra una advertencia en el summary y se continúa.

## Troubleshooting (problemas comunes)

- Error de parsing en Dependabot (interval = ""): indica que existe una entrada con `interval: ""` en `.github/dependabot.yml`. Soluciones:
  - Ejecutar el reusable con un `schedule_interval` válido (p. ej. `weekly`) para que sobrescriba la entrada.
  - Ejecutar en modo bajo demanda (`schedule_interval: ''`) para eliminar la entrada problemática.

- `gh: Not Found (HTTP 404)` al invocar `dependabot/updates`: comprobar que Dependabot Updates esté habilitado en Settings → Code security and analysis y que el token tenga permisos.

- Faltan utilidades en el runner (`jq`, `gh`): recomendamos `ubuntu-latest` o asegurarse de instalar `jq` si tu organización lo requiere para parseo.

## FAQ

- ¿El workflow crea PRs por sí mismo? No. En modo programado escribe/actualiza la configuración y Dependabot (el servicio) creará PRs según el intervalo. En modo bajo demanda solicita a Dependabot un escaneo inmediato que puede generar PRs.
- ¿Puedo invocar varias veces en paralelo? Sí. El reusable incluye lógica de merge y reintentos para minimizar conflictos; sin embargo puede haber reintentos si muchas invocaciones compiten simultáneamente.

## Buenas prácticas

- Usa `schedule_interval` sólo cuando quieras programación persistente. Para comprobaciones ad-hoc, integra el reusable con `schedule_interval: ''`.
- Verifica permisos y que Dependabot Updates/Alerts estén habilitados en el repositorio/organización.
- Si necesitas comportamientos especiales (prefijos de commit, etiquetas distintas, reglas de ignore adicionales), extiende el reusable o pásalos como parámetros de entrada.

---

Si quieres, puedo aplicar una versión similar de este README al directorio raíz o añadir ejemplos adicionales (por ejemplo, script para instalar `jq` en runners personalizados). 