# Workflow Reusable de Dependabot

Este workflow permite implementar Dependabot de forma automatizada y parametrizable en cualquier repositorio de GitHub, con la opción de ejecutarse bajo demanda o con programación.

## ¿Qué es Dependabot?

Dependabot es una herramienta de GitHub que automatiza la gestión de dependencias en tu proyecto. Detecta cuando hay actualizaciones disponibles para las dependencias de tu proyecto y crea pull requests para actualizarlas.

## Características del Workflow

- **Simple y directo**: Diseñado para ser fácil de implementar y usar.
- **Ejecución bajo demanda**: Puede ejecutarse como parte de un pipeline de CI/CD.
- **Ejecución programada**: También puede configurarse con una programación.
- **Auto-aprobación**: Opción para aprobar automáticamente los PRs de Dependabot.
- **Auto-fusión**: Opción para fusionar automáticamente los PRs aprobados.

## Cómo implementar

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
    uses: usuario/reusable-workflows/security/dependency-check/dependabot-workflow.yml@main
    with:
      package_ecosystem: "npm"        # Ecosistema de paquetes (npm, pip, maven, etc.)
      directory: "/"                  # Directorio donde se encuentra el archivo de dependencias
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
    uses: usuario/reusable-workflows/security/dependency-check/dependabot-workflow.yml@main
    with:
      package_ecosystem: "npm"        # Ecosistema de paquetes (npm, pip, maven, etc.)
      directory: "/"                  # Directorio donde se encuentra el archivo de dependencias
      schedule_interval: "weekly"     # Frecuencia de verificación
      auto_approve: true              # Aprobar automáticamente PRs
      auto_merge: true                # Fusionar automáticamente PRs
```

### 2. Parámetros disponibles

| Parámetro | Descripción | Requerido | Valor por defecto |
|-----------|-------------|-----------|-------------------|
| `package_ecosystem` | Ecosistema de paquetes (npm, pip, maven, docker, etc.) | Sí | - |
| `directory` | Directorio donde se encuentra el archivo de dependencias | Sí | - |
| `schedule_interval` | Frecuencia de verificación (daily, weekly, monthly). Si está vacío, se ejecuta bajo demanda | No | "" |
| `open_pull_requests_limit` | Límite de PRs abiertos simultáneamente | No | 10 |
| `auto_approve` | Aprobar automáticamente PRs de Dependabot | No | false |
| `auto_merge` | Fusionar automáticamente PRs de Dependabot | No | false |
| `allow_major_versions` | Permitir actualizaciones de versiones mayores | No | false |

### 3. Permisos necesarios

Para que el workflow funcione correctamente, necesitas configurar los siguientes permisos:

```yaml
permissions:
  contents: write       # Para crear/actualizar archivos
  pull-requests: write  # Para gestionar PRs
```

### 4. Modo de ejecución bajo demanda vs programado

Este workflow puede funcionar de dos maneras:

1. **Modo bajo demanda**: Si no especificas un `schedule_interval` (o lo dejas vacío), el workflow ejecutará una verificación inmediata de dependencias cuando sea invocado. Esto es útil para integrarlo en pipelines de CI/CD.

2. **Modo programado**: Si especificas un `schedule_interval` (daily, weekly, monthly), el workflow configurará Dependabot para que realice verificaciones periódicas según el intervalo especificado.

### 5. Solución de problemas

- **No se crean PRs**: Verifica que el ecosistema y directorio sean correctos.
- **Errores de permisos**: Asegúrate de que el workflow tenga los permisos necesarios.
- **Problemas con auto-merge**: Verifica la configuración de protección de ramas en tu repositorio.

### 4. Ejemplos de uso

#### Configuración básica para un proyecto Node.js

```yaml
uses: usuario/reusable-workflows/security/dependency-check/dependabot-workflow.yml@main
with:
  package_ecosystem: "npm"
  directory: "/"
  schedule_interval: "weekly"
```

#### Configuración completa para un proyecto Python con auto-aprobación

```yaml
uses: usuario/reusable-workflows/security/dependency-check/dependabot-workflow.yml@main
with:
  package_ecosystem: "pip"
  directory: "/"
  schedule_interval: "daily"
  open_pull_requests_limit: 5
  auto_approve: true
  auto_merge: true
  auto_merge_dependency_type: "all"
  versioning_strategy: "increase-if-necessary"
  allow_major_versions: false
  notify_assignees: true
  notify_reviewers: true
```

## Solución de problemas

### El workflow no crea la configuración de Dependabot

Asegúrate de que el token de GitHub tenga permisos suficientes para escribir en el repositorio.

### Los PRs no se aprueban automáticamente

Verifica que el parámetro `auto_approve` esté configurado como `true` y que el token tenga permisos para escribir en los pull requests.

### Los PRs no se fusionan automáticamente

Asegúrate de que tanto `auto_approve` como `auto_merge` estén configurados como `true` y que el token tenga permisos para escribir en el contenido del repositorio.