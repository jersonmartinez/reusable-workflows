# Reusable Workflows para GitHub Actions

Colección de workflows reutilizables para GitHub Actions que cubren el ciclo completo de DevOps y DevSecOps, diseñados para ser invocados desde otros workflows.

> ℹ️ **Nota:** Todos los workflows reutilizables viven bajo `.github/workflows/`. Al invocarlos desde otro repositorio, referencia siempre la ruta completa dentro de esa carpeta.

## Estructura del Repositorio

```
reusable-workflows/
├── .github/
│   └── workflows/                 # Workflows reutilizables listos para importar
│       ├── build-workflow.yml     # Pipeline de compilación multi-lenguaje
│       ├── dependabot-workflow.yml# Gestión automatizada de dependencias
│       ├── sast-workflow.yml      # Análisis estático de seguridad
│       └── test-workflow.yml      # Ejecución de suites de pruebas
├── docs/                          # Documentación, guías y notebooks de prueba
│   ├── ci-cd/                     # Guías específicas de CI/CD
│   ├── infrastructure/            # Material de infraestructura como código
│   ├── quality/                   # Documentación de calidad de código
│   └── security/
│       └── dependency-check/      # Documentación del workflow de Dependabot
├── templates/                     # Plantillas y ejemplos para consumidores
└── LICENSE
```

## Workflows Disponibles

### CI/CD

- **build-workflow** (`.github/workflows/build-workflow.yml`): Compilación para diferentes lenguajes y plataformas. Documentación relacionada en `docs/ci-cd/build/`.
- **test-workflow** (`.github/workflows/test-workflow.yml`): Orquesta pruebas unitarias, integración y end-to-end. Guías en `docs/ci-cd/test/`.
- **deploy-workflow**: En preparación.

### Seguridad

- **sast-workflow** (`.github/workflows/sast-workflow.yml`): Ejecuta análisis estático de seguridad. Referencias en `docs/security/sast/`.
- **dependabot-workflow** (`.github/workflows/dependabot-workflow.yml`): Automatiza Dependabot con opciones de programación, auto-aprobación y resumen de PRs. Documentación oficial en `docs/security/dependency-check/README.md`.
- **dast-workflow**: En preparación.

### Calidad de Código

- Workflows de lint y code review: En preparación (ver avance en `docs/quality/`).

### Infraestructura

- Workflows de Terraform y Kubernetes: En preparación (consultar `docs/infrastructure/`).

## Cómo Usar

Para utilizar estos workflows en tu repositorio, debes referenciarlos en tus propios workflows de GitHub Actions apuntando a la nueva ruta dentro de `.github/workflows`. Ejemplo:

```yaml
name: Mi Workflow

on:
  push:
    branches: [ main ]

jobs:
  build:
    uses: usuario/reusable-workflows/.github/workflows/ci-cd/build/build-workflow.yml@main
    with:
      language: 'java'
      version: '17'
```

## Contribución

Las contribuciones son bienvenidas. Por favor, revisa las guías de contribución en el archivo CONTRIBUTING.md.

## Licencia

Este proyecto está licenciado bajo [LICENSE](LICENSE).
