# Reusable Workflows para GitHub Actions

Colección de workflows reutilizables para GitHub Actions que cubren el ciclo completo de DevOps y DevSecOps, diseñados para ser invocados desde otros workflows.

## Estructura del Repositorio

```
reusable-workflows/
├── .github/
│   └── workflows/         # Workflows para el propio repositorio
├── ci-cd/                 # Workflows de Integración y Despliegue Continuo
│   ├── build/             # Workflows para compilación
│   ├── test/              # Workflows para pruebas
│   ├── deploy/            # Workflows para despliegue
│   └── docs/              # Documentación específica de CI/CD
├── security/              # Workflows de Seguridad
│   ├── sast/              # Análisis estático de seguridad
│   ├── dast/              # Análisis dinámico de seguridad
│   ├── dependency-check/  # Verificación de dependencias
│   └── docs/              # Documentación específica de seguridad
├── quality/               # Workflows de Calidad de Código
│   ├── linting/           # Análisis de código
│   ├── code-review/       # Revisión de código automatizada
│   └── docs/              # Documentación específica de calidad
├── infrastructure/        # Workflows para Infraestructura como Código
│   ├── terraform/         # Workflows para Terraform
│   ├── kubernetes/        # Workflows para Kubernetes
│   └── docs/              # Documentación específica de infraestructura
├── templates/             # Plantillas y ejemplos de uso
└── docs/                  # Documentación general
```

## Workflows Disponibles

### CI/CD

- **build-workflow**: Compilación para diferentes lenguajes y plataformas
- **test-workflow**: Ejecución de pruebas unitarias, integración y e2e
- **deploy-workflow**: Despliegue a diferentes entornos (dev, staging, prod)

### Seguridad

- **sast-workflow**: Análisis estático de seguridad
- **dast-workflow**: Análisis dinámico de seguridad
- **dependency-check-workflow**: Verificación de vulnerabilidades en dependencias

### Calidad de Código

- **lint-workflow**: Análisis de código para diferentes lenguajes
- **code-review-workflow**: Revisión automatizada de código

### Infraestructura

- **terraform-workflow**: Validación, planificación y aplicación de configuraciones Terraform
- **kubernetes-workflow**: Validación y despliegue de recursos Kubernetes

## Cómo Usar

Para utilizar estos workflows en tu repositorio, debes referenciarlos en tus propios workflows de GitHub Actions. Ejemplo:

```yaml
name: Mi Workflow

on:
  push:
    branches: [ main ]

jobs:
  build:
    uses: usuario/reusable-workflows/.github/workflows/build-workflow.yml@main
    with:
      language: 'java'
      version: '17'
```

## Contribución

Las contribuciones son bienvenidas. Por favor, revisa las guías de contribución en el archivo CONTRIBUTING.md.

## Licencia

Este proyecto está licenciado bajo [LICENSE](LICENSE).
