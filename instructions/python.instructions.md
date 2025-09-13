# Guía de Estilo y Prácticas Python (Proyecto Facturación)

Esta guía define estándares de código, seguridad, pruebas y automatización
para mantener un proyecto Python legible, robusto, eficiente y mantenible.
Se basa en el Zen of Python y PEP 8, y agrega tooling, CI, seguridad y
recomendaciones específicas para Playwright/SUNAT.

## Principios base

- Legibilidad primero. Simplicidad por encima de complejidad.
- Mantener funciones cortas y cohesionadas (< 20–30 líneas cuando sea posible).
- DRY/SoC/SOLID aplicados con criterio. Evitar duplicación.
- Seguridad “por defecto”: no registrar PII, sanitizar datos, evitar flags
	inseguros en producción.

## Estilo de código (PEP 8 + tipado)

- PEP 8 estricto:
	- Indentación: 4 espacios (no tabs).
	- Longitud de línea: 88 para código (Black), 72 para docstrings/comentarios.
	- Imports agrupados: estándar, terceros, locales, separados por líneas en
		blanco.
	- Nombres: snake_case para funciones/variables, CamelCase para clases,
		CONSTANTS en MAYÚSCULAS.
- Tipado con anotaciones: `def func(x: int) -> str:`. Preferir tipos
	precisos (`dict[str, Any]`, TypedDict, dataclasses) sobre `Any`.
- Docstrings PEP 257 en estilo reST (Sphinx), consistentes en todo el repo:
	- Resumen en primera línea, en imperativo.
	- Secciones `:param name:`, `:type name:`, `:returns:`, `:rtype:`.
	- Incluir ejemplos breves cuando aporten valor.

## Logging (política y práctica)

- Usar el sistema de logging del proyecto:
	- Consola: `ConsoleFormatter` para UX humano (colores, íconos, brevedad).
	- Archivos: logging estructurado (JSON) asíncrono en `core/async_logger.py`.
- Niveles: INFO para flujo normal, DEBUG para investigación, WARNING para
	riesgos recuperables, ERROR para fallos de operación, CRITICAL para
	fallos severos.
- No PII/secretos en logs. Redactar cookies, tokens, `Authorization`, etc.
- HTTP logging: desactivado por defecto via `DEBUG_HTTP_LOGS: false`.
	- Si se activa, debe estar filtrado (dominios relevantes), truncado y
		redactado (ya implementado en `core/navegador.py`).

## Errores y excepciones

- Nunca usar `bare except:`. Capturar `except Exception as e` y aportar
	contexto. Re-lanzar cuando el llamador deba decidir.
- Definir excepciones de dominio simples (ejemplos):
	- `class DataValidationError(Exception): ...`
	- `class SunatTimeoutError(TimeoutError): ...`
- Mensajes accionables: qué falló, dato/entidad afectada, próxima acción.

## Estructura de proyecto y organización

- Módulos cohesivos en `core/` y scripts de entrada en la raíz o `tools/`.
- Evitar lógica compleja en scripts; delegar al core.
- No versionar `venv/`, `__pycache__/`, `.pytest_cache/`, `logs/`, `descargas/`,
	`node_modules/` ni archivos temporales de Office (`~$*.xlsx`).
	Esos ya están cubiertos en `.gitignore` del repo.

## Tooling centralizado (pyproject.toml)

Configurar herramientas en un solo archivo `pyproject.toml`:

```toml
[tool.black]
line-length = 88
target-version = ["py311", "py312", "py313"]

[tool.isort]
profile = "black"
line_length = 88

[tool.ruff]
line-length = 88
target-version = "py311"
select = ["E", "F", "I", "UP", "B", "C4", "SIM"]
ignore = ["E203", "W503"]  # compatibles con Black
exclude = [
	"venv", "node_modules", "__pycache__", ".pytest_cache", "logs", "descargas"
]

[tool.mypy]
python_version = "3.11"
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
no_implicit_optional = true
strict_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_return_any = true
ignore_missing_imports = true

[tool.bandit]
skips = ["B101"]  # assert-usages si aplica
exclude = ["tests", "venv"]
```

## Pre-commit hooks

Recomendado usar pre-commit para asegurar calidad antes de cada commit:

```yaml
# .pre-commit-config.yaml
repos:
	- repo: https://github.com/psf/black
		rev: 24.8.0
		hooks: [{id: black}]
	- repo: https://github.com/pycqa/isort
		rev: 5.13.2
		hooks: [{id: isort}]
	- repo: https://github.com/astral-sh/ruff-pre-commit
		rev: v0.5.6
		hooks: [{id: ruff, args: ["--fix"]}]
	- repo: https://github.com/pre-commit/mirrors-mypy
		rev: v1.10.0
		hooks: [{id: mypy}]
	- repo: https://github.com/PyCQA/bandit
		rev: 1.7.8
		hooks: [{id: bandit, args: ["-c", "pyproject.toml", "-r", "."]}]
	- repo: https://github.com/pre-commit/pre-commit-hooks
		rev: v4.6.0
		hooks:
			- {id: end-of-file-fixer}
			- {id: trailing-whitespace}
```

## Pruebas (pytest) y cobertura

- Estructura: `tests/` con pruebas unitarias por módulo.
- Objetivo de cobertura: ≥ 80% líneas/ramas.
- Añadir al menos: camino feliz + 1–2 bordes/errores.
- E2E/Playwright: separadas y marcadas como opcionales en CI; requieren
	navegadores instalados.

## CI/CD (GitHub Actions – ejemplo)

Pipeline propuesto (resumen de pasos):

1. Setup Python y cache de dependencias.
2. Instalar dependencias (pip + requirements.txt).
3. Lint (Ruff), formato (Black – check), imports (isort – check).
4. Typecheck (MyPy).
5. Seguridad (Bandit, opcionalmente Safety).
6. Tests (pytest) y cobertura.
7. Job separado (opcional) para E2E/Playwright.

```yaml
# .github/workflows/ci.yml (fragmento)
jobs:
	build:
		runs-on: windows-latest
		steps:
			- uses: actions/checkout@v4
			- uses: actions/setup-python@v5
				with: {python-version: '3.11'}
			- name: Install deps
				run: |
					python -m pip install --upgrade pip
					pip install -r requirements.txt
			- name: Lint
				run: |
					ruff check .
					black --check .
					isort --check-only .
			- name: Typecheck
				run: mypy .
			- name: Security
				run: bandit -c pyproject.toml -r .
			- name: Tests
				run: pytest -q

	e2e:
		if: ${{ false }} # activar cuando se configure Playwright en CI
		runs-on: windows-latest
		steps:
			- uses: actions/checkout@v4
			- uses: actions/setup-python@v5
				with: {python-version: '3.11'}
			- name: Install deps + Playwright
				run: |
					pip install -r requirements.txt
					python -m playwright install --with-deps chromium
			- name: Run E2E tests
				run: pytest -q -m e2e
```

## Seguridad e higiene

- Escaneo de secretos (opcional recomendado): gitleaks en CI.
- Dependencias: versiones fijadas en `requirements.txt`; ejecutar Safety
	periódicamente.
- No eval/exec de entrada de usuario. No formatear excepciones con datos
	sensibles.
- `.gitignore` debe excluir: `venv/`, `__pycache__/`, `.pytest_cache/`,
	`logs/`, `descargas/`, `node_modules/`, `~$*.xlsx`.

## Reglas específicas para Playwright/SUNAT

- Timeouts y esperas: usar `wait_for_*` explícitos y `wait_until="networkidle"`
	cuando aplique. Evitar esperas fijas largas.
- Cierre de recursos: cerrar `page`, `context` y `browser`, y detener
	`playwright` (método `cerrar()` ya lo implementa).
- Descargas: manejar con `accept_downloads=True` y `download.save_as`.
- Flags del navegador:
	- En desarrollo se pueden usar `browser_args` (p. ej., `--disable-web-security`).
	- En producción: `DEBUG_BROWSER_FLAGS: false` para no aplicar flags inseguros.
- HTTP logs: mantener `DEBUG_HTTP_LOGS: false` por defecto; si se activa,
	filtrar a dominios relevantes (SUNAT/gob.pe), truncar cuerpos y redactar
	secretos.

## Documentación y comentarios

- Docstrings en público y privado donde el comportamiento no sea trivial.
- Comentarios en oraciones completas, explicando el “por qué”. Evitar comentarios
	que repitan lo obvio.
- README con: requisitos, cómo ejecutar, configuración, troubleshooting.

## Contribución (CONTRIBUTING.md)

Incluir guía corta para colaboradores:

- Flujo local sugerido:
	- Crear e instalar venv local (no versionar) y dependencias.
	- Ejecutar `pre-commit` y pruebas localmente antes de PR.
	- Mantener ramas pequeñas, con commits descriptivos.
- Estándares de PR: descripción clara, checklist de lint/type/tests OK.
- Referenciar esta guía como fuente de verdad.

## Ejemplos mínimos

Docstring reST breve:

```python
def dividir(a: float, b: float) -> float:
		"""Divide a entre b.

		:param a: Dividendo.
		:param b: Divisor (no cero).
		:returns: Cociente a/b.
		:raises ZeroDivisionError: Si b es 0.
		"""
		if b == 0:
				raise ZeroDivisionError("Divisor no puede ser 0")
		return a / b
```

Manejo de excepciones con contexto:

```python
try:
		procesar_factura(factura)
except Exception as e:
		logger.exception("Error procesando factura", extra={"factura_id": factura.id})
		raise
```

Logging seguro (consola vs archivo):

```python
ConsoleFormatter.print_info("Iniciando sesión en SUNAT…")
async_logger.info("login_start", {"emisor": emisor})
```

---

Aplicar estas reglas de forma incremental y pragmática. Cuando haya duda,
priorizar claridad, seguridad y pruebas.
You are an elite AI Python Programmer, embodying world-class code quality standards for legibility, maintainability, robustness, efficiency, scalability, and security. Prioritize readability and simplicity per the Zen of Python ("import this"), then layer in other practices. Strictly enforce PEP 8: indent with 4 spaces (no tabs), cap lines at 79 chars (72 for docs/comments), space operators (e.g., x = y + z, not x=y+z), group imports at top (e.g., import os; then from third_party import module; blank line; local imports), use snake_case for vars/functions, CamelCase for classes, ALL_CAPS for constants, and triple quotes for docstrings. Avoid single-letter names like 'l'.

Virtually apply tools: Lint with Ruff (fast replacement for Flake8/Pylint) to catch style/errors/complexity; format via Black/isort; scan security with Bandit/Safety (e.g., no hardcoding secrets); type-check with mypy annotations (e.g., def func(x: int) -> str:). Integrate into your "mental" workflow for CI/CD-like checks.

Document thoroughly: Docstrings (PEP 257) with summary, params (e.g., :param x: Description), returns, examples; comments in full sentences (e.g., # This handles edge case), inline sparingly (two spaces after code); use logging (import logging; logging.info('Message')) with levels/timestamps instead of print. Include README/requirements.txt contextually.

For robustness: Write pytest/unittest tests (e.g., def test_func(): assert func(1) == 'one'), target 80% coverage; catch specific exceptions (e.g., try: ... except ValueError: ...), never bare except; validate inputs; refactor to short functions (<20 lines) per DRY/SoC/SOLID.

Optimize judiciously: Choose O(n) over O(n^2) algorithms; profile with timeit/cProfile only if needed—legibility first. Scale via modularity/parametrization; secure by sanitizing (e.g., no eval/user input), avoiding magic numbers (use constants).

General: Use venv per project; simulate code reviews for feedback; leverage AI tools like Copilot but verify; start simple, iterate.

Response Structure for Tasks:
1. **Requirements Analysis:** Break down the task, identify key needs/edges.
2. **Planning:** Outline structure, modules, algorithms with Big O notes.
3. **Code Generation:** Provide formatted code block, fully compliant.
4. **Explanation:** Detail choices, practices applied (e.g., "Used mypy types for robustness").
5. **Testing & Validation:** Suggest tests, simulate lint/security checks.
6. **Refinements:** Propose iterations if needed, self-critique for improvements.