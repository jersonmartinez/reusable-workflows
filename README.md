# Reusable Workflows para GitHub Actions

Colección de workflows reutilizables para GitHub Actions que cubren el ciclo completo de DevOps y DevSecOps, diseñados para ser invocados desde otros workflows.

> ℹ️ **Nota:** Todos los workflows reutilizables viven bajo `.github/workflows/`. Al invocarlos desde otro repositorio, referencia siempre la ruta completa dentro de esa carpeta.

## Estructura del Repositorio

```
reusable-workflows/
├── .github/
│   └── workflows/         # Catálogo de workflows reutilizables por dominio
│       ├── ci-cd/         # Integración y Despliegue Continuo
│       │   ├── build/     # Workflows de compilación
│       │   ├── deploy/    # Workflows de despliegue
│       │   └── test/      # Workflows de pruebas
│       ├── quality/       # Flujos de calidad de código (lint, code review)
│       ├── security/      # Flujos de DevSecOps (SAST, DAST, documentación de dependencias)
│       └── infrastructure/# Infraestructura como código (Terraform, Kubernetes)
├── docs/                  # Documentación transversal
└── templates/             # Plantillas y ejemplos de uso
```

## Workflows Disponibles

### CI/CD

- **build-workflow** (`.github/workflows/ci-cd/build/build-workflow.yml`): Compilación para diferentes lenguajes y plataformas
- **test-workflow** (`.github/workflows/ci-cd/test/test-workflow.yml`): Ejecución de pruebas unitarias, integración y e2e
- **deploy-workflow**: Despliegue a diferentes entornos (dev, staging, prod) *(en preparación)*

### Seguridad

- **sast-workflow** (`.github/workflows/security/sast/sast-workflow.yml`): Análisis estático de seguridad
- **dast-workflow**: Análisis dinámico de seguridad *(en preparación)*
- **dependency-check-workflow** (`.github/workflows/dependabot-workflow.yml`): Verificación de vulnerabilidades en dependencias (documentación en `.github/workflows/security/docs/dependency-check/README.md`)

### Calidad de Código

- **lint-workflow**: Análisis de código para diferentes lenguajes *(en preparación)*
- **code-review-workflow**: Revisión automatizada de código *(en preparación)*

### Infraestructura

- **terraform-workflow**: Validación, planificación y aplicación de configuraciones Terraform *(en preparación)*
- **kubernetes-workflow**: Validación y despliegue de recursos Kubernetes *(en preparación)*

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
