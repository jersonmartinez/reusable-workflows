# 🛡️ Dependabot Report & Management Workflow

Este workflow reusable está diseñado para centralizar la gestión, monitoreo y reporte de las actualizaciones de dependencias detectadas por **Dependabot**. Su objetivo principal es transformar las notificaciones dispersas de Pull Requests en reportes ejecutivos consolidados (Issue, HTML, PDF) y mantener limpio el listado de PRs del repositorio.

Está orientado a equipos de **Desarrollo**, **Seguridad** y **DevOps** que necesitan visibilidad sobre la deuda técnica y vulnerabilidades sin el ruido de múltiples PRs abiertos simultáneamente.

---

## 📋 Tabla de Contenidos

- [🛡️ Dependabot Report \& Management Workflow](#️-dependabot-report--management-workflow)
  - [📋 Tabla de Contenidos](#-tabla-de-contenidos)
  - [🚀 Características Principales](#-características-principales)
  - [🔄 Flujo de Trabajo](#-flujo-de-trabajo)
  - [✅ Requisitos Previos](#-requisitos-previos)
  - [📖 Guía de Implementación](#-guía-de-implementación)
    - [Uso Básico](#uso-básico)
    - [Configuración Completa](#configuración-completa)
  - [⚙️ Referencia de Parámetros (Inputs)](#️-referencia-de-parámetros-inputs)
  - [🔐 Permisos Requeridos](#-permisos-requeridos)
  - [🛠️ Detalles Técnicos y Limitaciones](#️-detalles-técnicos-y-limitaciones)
    - [Lo que NO hace este workflow](#lo-que-no-hace-este-workflow)
    - [Mecanismo de "Trigger Now"](#mecanismo-de-trigger-now)
    - [Estructura de Reportes](#estructura-de-reportes)
  - [📦 Salidas y Artefactos](#-salidas-y-artefactos)

---

## 🚀 Características Principales

| Característica | Descripción |
| :--- | :--- |
| **📊 Reportes Ejecutivos** | Genera reportes detallados en formato **PDF** y **HTML** con métricas, gráficas y tablas de resumen. |
| **📝 Issue de Resumen** | Crea o actualiza un Issue en GitHub con una tabla resumen de todos los PRs de Dependabot abiertos. |
| **🧹 Limpieza Automática** | Opción para cerrar automáticamente los PRs de Dependabot (`close_dependabot_prs`) para evitar ruido, centralizando la gestión en el reporte. |
| **⚡ Trigger bajo Demanda** | Capacidad de forzar la ejecución de Dependabot (`trigger_dependabot_now`) modificando el fichero de configuración. |
| **🚨 Alertas de Seguridad** | Recopila y resume las alertas de seguridad (Dependabot Alerts) activas en el repositorio. |
| **🎨 Personalizable** | Permite configurar logos, nombre de la empresa y títulos de los reportes. |

---

## 🔄 Flujo de Trabajo

```mermaid
graph TD
    A[Caller Workflow] -->|Llama a| B(Dependabot Report Workflow)
    B --> C{Trigger Now?}
    C -- Sí --> D[Modificar dependabot.yml]
    D --> E[Esperar PRs (Polling)]
    C -- No --> F[Detectar PRs existentes]
    E --> F
    F --> G[Recopilar Alertas de Seguridad]
    G --> H[Crear/Actualizar Issue de Reporte]
    H --> I[Generar PDF y HTML]
    I --> J{Cerrar PRs?}
    J -- Sí --> K[Cerrar PRs de Dependabot]
    J -- No --> L[Mantener PRs abiertos]
    K --> M[Publicar Artefactos]
    L --> M
    M --> N[Comentar en Issue con Links]
```

---

## ✅ Requisitos Previos

Para que este workflow funcione correctamente, debes asegurarte de cumplir con lo siguiente:

1.  **Configuración de Dependabot**: El repositorio debe tener ya configurado el fichero `.github/dependabot.yml`. Este workflow **no crea** la configuración de Dependabot, solo la gestiona y reporta.
2.  **Permisos del Token**: El `GITHUB_TOKEN` utilizado debe tener permisos suficientes (ver sección de Permisos).
3.  **Secretos (Opcional)**: Si utilizas registros privados, asegúrate de que Dependabot tenga acceso a ellos, aunque este workflow opera a nivel de gestión de PRs y no de instalación de paquetes.

---

## 📖 Guía de Implementación

### Uso Básico

Para integrar este reporte en tu repositorio, crea un archivo en `.github/workflows/dependabot-check.yml`:

```yaml
name: 🛡️ Security - Dependabot Report

on:
  # Ejecutar semanalmente o cuando se desee
  schedule:
    - cron: '0 6 * * 1' # Lunes a las 6:00 AM
  workflow_dispatch:

jobs:
  dependabot-report:
    uses: jersonmartinez/reusable-workflows/.github/workflows/dependabot-report.yml@main
    with:
      create_issue: true
      close_dependabot_prs: true
    permissions:
      contents: write
      pull-requests: write
      issues: write
      security-events: read
```

### Configuración Completa

Ejemplo con todas las capacidades habilitadas, incluyendo trigger inmediato y personalización de marca:

```yaml
name: 🛡️ Security - Dependabot Report Full

on:
  workflow_dispatch:
    inputs:
      trigger_now:
        description: 'Forzar ejecución de Dependabot ahora'
        type: boolean
        default: false

jobs:
  dependabot-report:
    uses: jersonmartinez/reusable-workflows/.github/workflows/dependabot-report.yml@main
    with:
      # Comportamiento
      trigger_dependabot_now: ${{ inputs.trigger_now }}
      wait_minutes: 15          # Esperar hasta 15 min si se disparó la ejecución
      close_dependabot_prs: true # Cerrar PRs para limpiar el board
      
      # Reportes
      create_issue: true
      issue_title: '🛡️ Reporte Semanal de Dependencias: ${date}'
      generate_pdf_report: true
      generate_html_report: true
      
      # Personalización
      company_name: 'Mi Empresa S.A.'
      logo_url: 'https://mi-empresa.com/logo.png'
      
    permissions:
      contents: write       # Necesario para trigger_dependabot_now (git push)
      pull-requests: write  # Necesario para cerrar PRs
      issues: write         # Necesario para crear el Issue
      security-events: read # Necesario para leer alertas
```

---

## ⚙️ Referencia de Parámetros (Inputs)

| Input | Tipo | Default | Descripción |
| :--- | :--- | :--- | :--- |
| `create_issue` | `boolean` | `true` | Crea un Issue en GitHub con el resumen de los hallazgos. |
| `issue_title` | `string` | `Reporte...` | Título del Issue. Soporta `${date}` como variable. |
| `close_dependabot_prs` | `boolean` | `true` | Si es `true`, cierra los PRs de Dependabot detectados para reducir ruido. |
| `trigger_dependabot_now` | `boolean` | `false` | Si es `true`, modifica `dependabot.yml` para forzar una ejecución inmediata. |
| `wait_minutes` | `number` | `5` | Tiempo de espera (polling) para detectar nuevos PRs si se activó el trigger. |
| `dependabot_config_path` | `string` | `.github/dependabot.yml` | Ruta al fichero de configuración de Dependabot. |
| `generate_pdf_report` | `boolean` | `false` | Genera un archivo PDF descargable con el reporte completo. |
| `generate_html_report` | `boolean` | `true` | Genera un archivo HTML interactivo con el reporte. |
| `company_name` | `string` | `PRB` | Nombre de la empresa para el encabezado de los reportes. |
| `logo_url` | `string` | `...` | URL del logo a incluir en los reportes HTML/PDF. |
| `dry_run_close` | `boolean` | `false` | Simula el cierre de PRs sin ejecutar la acción real (para pruebas). |
| `skip_close_labels` | `string` | `''` | Lista de etiquetas (separadas por coma) que evitarán que un PR sea cerrado automáticamente. |

---

## 🔐 Permisos Requeridos

Este workflow realiza acciones privilegiadas. Asegúrate de otorgar los siguientes permisos en el job que llama al workflow (`caller`):

```yaml
permissions:
  contents: write       # Requerido si usas trigger_dependabot_now (hace commit)
  pull-requests: write  # Requerido para listar y cerrar PRs
  issues: write         # Requerido para crear/editar el Issue de reporte
  security-events: read # Requerido para leer alertas de seguridad (Dependabot Alerts)
```

> [!WARNING]
> Si no proporcionas `contents: write` y activas `trigger_dependabot_now`, el workflow fallará al intentar modificar el archivo de configuración.

---

## 🛠️ Detalles Técnicos y Limitaciones

### Lo que NO hace este workflow
*   ❌ **No configura Dependabot desde cero**: Aunque existen pasos en el código fuente relacionados con la generación de configuración (`Generate Dependabot Config`), estos están actualmente deshabilitados (`if: false`). Se asume que ya tienes un `dependabot.yml` válido.
*   ❌ **No valida etiquetas (Labels)**: La lógica de validación y creación de etiquetas de ecosistemas también está deshabilitada en la versión actual.
*   ❌ **No resuelve conflictos**: Si un PR de Dependabot tiene conflictos, este workflow solo lo reporta, no intenta arreglarlo.

### Mecanismo de "Trigger Now"
La funcionalidad `trigger_dependabot_now` funciona mediante un "hack" benigno: añade un comentario con la fecha actual al final del archivo `dependabot.yml` y hace un commit. Esto es detectado por GitHub como un cambio en la configuración, lo que dispara inmediatamente la búsqueda de actualizaciones por parte de Dependabot.

### Estructura de Reportes
*   **SemVer**: Los reportes clasifican las actualizaciones en `major`, `minor` y `patch` basándose en el análisis semántico de las versiones.
*   **Prioridad**: Se destacan las actualizaciones de seguridad críticas.

---

## 📦 Salidas y Artefactos

Al finalizar, el workflow produce:

1.  **Issue en GitHub**: Un resumen visible para todo el equipo.
2.  **Artefactos de Workflow**:
    *   `dependabot-report.pdf`: Documento formal para auditoría o management.
    *   `dependabot-report.html`: Vista web amigable.
    *   `debug-artifacts`: Logs y JSONs crudos (si `upload_debug_artifact` es true).

> [!TIP]
> Utiliza el reporte HTML para una navegación rápida y el PDF para archivar evidencias de cumplimiento de seguridad.
