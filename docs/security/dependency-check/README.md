# 🔁 Workflow Reusable de Dependabot

Este workflow permite implementar Dependabot de forma automatizada y parametrizable en cualquier repositorio de GitHub, con la opción de ejecutarse bajo demanda o con programación.

> 📍 **Ubicación:** `.github/workflows/dependabot-workflow.yml`

## 🤖 ¿Qué es Dependabot?

Dependabot es una herramienta de GitHub que automatiza la gestión de dependencias en tu proyecto. Detecta cuando hay actualizaciones disponibles para las dependencias de tu proyecto y crea pull requests para actualizarlas.

## ✨ Características del Workflow

- **Simple y directo**: Diseñado para ser fácil de implementar y usar.
- **Ejecución bajo demanda**: Puede ejecutarse como parte de un pipeline de CI/CD.
- **Ejecución programada**: También puede configurarse con una programación.
- **Auto-aprobación**: Opción para aprobar automáticamente los PRs de Dependabot.
- **Auto-fusión**: Opción para fusionar automáticamente los PRs aprobados.
- **Detección automática del manifiesto**: Identifica el archivo de dependencias según el ecosistema o permite definirlo manualmente.
- **Actualización idempotente**: Fusiona entradas en `.github/dependabot.yml` mediante la API de GitHub, evitando conflictos cuando se invoca el workflow desde varios jobs o repositorios.

## 🛠️ Cómo implementar

### 1. Referencia al workflow

#### Opción 1: Ejecución bajo demanda (como parte de un pipeline)

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    # ... otros pasos del pipeline ...
    
  check-dependencies:
    needs: build  # Ejecutar después de la compilación
    uses: usuario/reusable-workflows/.github/workflows/dependabot-workflow.yml@main
    with:
      package_ecosystem: "npm"        # Ecosistema de paquetes (npm, pip, maven, etc.)
      directory: "/"                  # Directorio donde se encuentra el archivo de dependencias
      dependency_file_path: "package.json"  # Opcional: ruta exacta del manifiesto
      auto_approve: true              # Aprobar automáticamente PRs
      auto_merge: true                # Fusionar automáticamente PRs
```

#### Opción 2: Ejecución programada

```yaml
name: Dependabot

on:
  schedule:
    - cron: '0 0 * * 1'  # Ejecutar cada lunes a medianoche
  workflow_dispatch:     # Permitir ejecución manual

jobs:
  dependabot:
    uses: usuario/reusable-workflows/.github/workflows/dependabot-workflow.yml@main
    with:
      package_ecosystem: "npm"        # Ecosistema de paquetes (npm, pip, maven, etc.)
      directory: "/"                  # Directorio donde se encuentra el archivo de dependencias
      schedule_interval: "weekly"     # Frecuencia de verificación
      auto_approve: true              # Aprobar automáticamente PRs
      auto_merge: true                # Fusionar automáticamente PRs
      auto_merge_label: "dependencies" # Etiqueta requerida para auto-merge
```

### 2. Parámetros disponibles

| Parámetro | Descripción | Requerido | Valor por defecto |
|-----------|-------------|-----------|-------------------|
| `package_ecosystem` | Ecosistema de paquetes (npm, pip, maven, docker, etc.) | Sí | - |
| `directory` | Directorio donde se encuentra el archivo de dependencias | Sí | - |
| `dependency_file_path` | Ruta exacta del archivo de dependencias. Si se omite, el workflow intenta detectarlo automáticamente según el ecosistema | No | Detectado automáticamente |
| `schedule_interval` | Frecuencia de verificación (daily, weekly, monthly). Si está vacío, se ejecuta bajo demanda | No | "" |
| `open_pull_requests_limit` | Límite de PRs abiertos simultáneamente | No | 10 |
| `auto_approve` | Aprobar automáticamente PRs de Dependabot | No | false |
| `auto_merge` | Fusionar automáticamente PRs de Dependabot | No | false |
| `auto_merge_label` | Etiqueta requerida para que un PR se auto-fusione. Dejar vacío para aplicar a todos los PRs del bot | No | "dependencies" |
| `allow_major_versions` | Permitir actualizaciones de versiones mayores. Si es `false`, se ignoran automáticamente las actualizaciones `semver-major` | No | false |

### 3. Permisos necesarios

Para que el workflow funcione correctamente, necesitas configurar los siguientes permisos:

```yaml
permissions:
  contents: write       # Para crear/actualizar archivos
  pull-requests: write  # Para gestionar PRs
  security-events: write # Necesario para ejecutar escaneos con Dependabot
```

### 4. Modo de ejecución bajo demanda vs programado

Este workflow puede funcionar de dos maneras:

1. **Modo bajo demanda**: Si no especificas un `schedule_interval` (o lo dejas vacío), el workflow omite la creación del archivo `.github/dependabot.yml` y lanza un escaneo inmediato mediante la API de Dependabot. Esto es útil para integrarlo en pipelines de CI/CD sin habilitar una programación recurrente.

2. **Modo programado**: Si especificas un `schedule_interval` (daily, weekly, monthly), el workflow genera o actualiza `.github/dependabot.yml` directamente a través de la API de GitHub. Cada invocación sustituye (o añade) la entrada correspondiente al par `package_ecosystem` + `directory`, por lo que puedes ejecutar el workflow varias veces en un mismo pipeline para cubrir diferentes rutas sin preocuparte por conflictos de git.

> ℹ️ **Aclaración terminológica:** `.github/dependabot.yml` es el archivo de configuración oficial que GitHub espera para Dependabot dentro de cada repositorio consumidor. No tiene relación con el nombre del workflow que uses para invocar esta plantilla (por ejemplo, `dependabot-exec.yml`). Puedes llamar al workflow desde cualquier archivo de Actions; la salida seguirá escribiendo o actualizando `.github/dependabot.yml`, que es donde Dependabot lee su configuración.

> 📌 **Nota:** Cuando `allow_major_versions` es `false`, el archivo de configuración añade reglas para ignorar las actualizaciones `semver-major` automáticamente.

> ⚠️ **Importante:** Cada invocación con `schedule_interval` actualiza (o reemplaza) la entrada que coincida con el par `package_ecosystem` + `directory`. Si necesitas modificar varias rutas, puedes invocar el workflow desde distintos jobs en un mismo run; cada uno añadirá o sustituirá únicamente su sección correspondiente.

### 5. Solución de problemas

- **No se crean PRs**: Verifica que el ecosistema y directorio sean correctos.
- **Errores de permisos**: Asegúrate de que el workflow tenga los permisos necesarios.
- **Problemas con auto-merge**: Verifica la configuración de protección de ramas en tu repositorio.

### 6. Resultado y resumen automático

Al finalizar, el workflow añade un resumen en la pestaña **Summary** de la ejecución con:

- Datos clave del run (repositorio, directorio, ecosistema y modo de ejecución).
- Un estado visual (✅/❌) indicando si el job terminó correctamente o con errores.
- El archivo evaluado o la confirmación de que se generó `.github/dependabot.yml` (incluyendo la entrada añadida).
- Una tabla con los PRs abiertos actualmente por `app/dependabot` (si existen) indicando número, título, rama base y URL. Si no hay PRs abiertos, lo deja señalado explícitamente.
- Un recordatorio de que, en modo programado, los PRs aparecerán cuando Dependabot procese la configuración (según el intervalo definido).

### 6. Ejemplos de uso

#### Configuración básica para un proyecto Node.js

```yaml
uses: usuario/reusable-workflows/.github/workflows/dependabot-workflow.yml@main
with:
  package_ecosystem: "npm"
  directory: "/"
  schedule_interval: "weekly"
```

#### Configuración completa para un proyecto Python con auto-aprobación

```yaml
uses: usuario/reusable-workflows/.github/workflows/dependabot-workflow.yml@main
with:
  package_ecosystem: "pip"
  directory: "/"
  schedule_interval: "daily"
  open_pull_requests_limit: 5
  auto_approve: true
  auto_merge: true
  dependency_file_path: "requirements.txt"
  allow_major_versions: false
```

## 🧯 Solución de problemas

### ❓ El workflow no crea la configuración de Dependabot

Asegúrate de que el token de GitHub tenga permisos suficientes para escribir en el repositorio.

### ❓ Los PRs no se aprueban automáticamente

Verifica que el parámetro `auto_approve` esté configurado como `true` y que el token tenga permisos para escribir en los pull requests.

### ❓ Los PRs no se fusionan automáticamente

Asegúrate de que tanto `auto_approve` como `auto_merge` estén configurados como `true` y que el token tenga permisos para escribir en el contenido del repositorio.