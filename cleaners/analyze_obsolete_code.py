#!/usr/bin/env python3
"""
Script avanzado para detectar código obsoleto en el proyecto Aqxion Scraper
"""

import os
import re
import ast
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple, Any
from collections import defaultdict, Counter

# Constants
MIN_BODY_LENGTH = 50
REPORT_WIDTH = 55

class CodeAnalyzer:
    """Analizador avanzado de código Python"""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.python_files = []
        self.issues = defaultdict(list)

    def find_python_files(self) -> None:
        """Encontrar todos los archivos Python en el proyecto"""  # REVIEW: Consider implementing  # REVIEW: Consider implementing
        exclude_dirs = {'.git', 'node_modules', 'venv', '.venv', 'env', '__pycache__'}

        for filepath in self.project_dir.rglob('*.py'):
            if not any(part in exclude_dirs for part in filepath.parts):
                self.python_files.append(filepath)

    def analyze_file(self, filepath: Path) -> Dict[str, Any]:
        """Analizar un archivo Python individual"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(filepath))
            analyzer = FileAnalyzer(filepath, content, tree)
            return analyzer.analyze()

        except SyntaxError as e:
            return {'syntax_error': str(e)}
        except Exception as e:
            return {'error': str(e)}

    def analyze_all_files(self) -> None:
        """Analizar todos los archivos Python"""  # REVIEW: Consider implementing  # REVIEW: Consider implementing
        print(f"🔍 Analizando {len(self.python_files)} archivos Python...")

        for filepath in self.python_files:
            print(f"  📄 Analizando: {filepath.name}")
            analysis = self.analyze_file(filepath)

            if 'error' in analysis or 'syntax_error' in analysis:
                continue

            # Agregar issues encontrados
            for issue_type, issues in analysis.items():
                if issues:  # Solo si hay issues
                    self.issues[issue_type].extend(issues)

    def generate_report(self) -> None:
        """Generar reporte de código obsoleto"""
        print("\n" + "="*70)
        print("📊 REPORTE DE CÓDIGO OBSOLETO")
        print("="*70)

        total_issues = sum(len(issues) for issues in self.issues.values())

        if total_issues == 0:
            print("✨ ¡Excelente! No se encontró código obsoleto significativo")
            return

        print(f"⚠️  Se encontraron {total_issues} issues potenciales:\n")

        # Reportar cada tipo de issue
        for issue_type, issues in self.issues.items():
            if not issues:
                continue

            print(f"🔸 {issue_type.upper().replace('_', ' ')} ({len(issues)}):")

            # Mostrar máximo 10 issues por tipo
            for issue in issues[:10]:
                if isinstance(issue, dict):
                    if 'line' in issue:
                        print(f"  📍 Línea {issue['line']}: {issue.get('message', issue.get('name', 'N/A'))}")
                    else:
                        print(f"  📍 {issue.get('name', issue.get('message', 'N/A'))}")
                else:
                    print(f"  📍 {issue}")

            if len(issues) > 10:
                print(f"  ... y {len(issues) - 10} más")

            print()

        # Recomendaciones
        self.print_recommendations()

    def print_recommendations(self) -> None:
        """Imprimir recomendaciones de limpieza"""
        print("💡 RECOMENDACIONES PARA LIMPIEZA:")
        print("-" * 40)

        if self.issues.get('unused_imports'):
            print("• Eliminar imports no utilizados")
        if self.issues.get('unused_variables'):
            print("• Remover variables no utilizadas")
        if self.issues.get('unused_functions'):
            print("• Eliminar funciones no utilizadas")
        if self.issues.get('dead_code'):
            print("• Remover código muerto/comentado")
        if self.issues.get('duplicate_code'):
            print("• Refactorizar código duplicado")
        if self.issues.get('complex_functions'):
            print("• Simplificar funciones complejas")
        if self.issues.get('long_functions'):
            print("• Dividir funciones largas")
        if self.issues.get('magic_numbers'):
            print("• Reemplazar números mágicos con constantes")

        print("\n🔧 Para automatizar la limpieza:")
        print("• Usar herramientas como: autopep8, black, flake8, pylint")
        print("• Configurar pre-commit hooks para calidad de código")
        print("• Implementar CI/CD con análisis estático")

class FileAnalyzer(ast.NodeVisitor):
    """Analizador de archivo individual"""

    def __init__(self, filepath: Path, content: str, tree: ast.AST):
        self.filepath = filepath
        self.content = content
        self.tree = tree
        self.lines = content.splitlines()

        # Estado del análisis
        self.defined_names = set()
        self.used_names = set()
        self.imported_names = set()
        self.function_defs = set()
        self.class_defs = set()

        # Issues encontrados
        self.issues = defaultdict(list)

    def analyze(self) -> Dict[str, List]:
        """Realizar análisis completo del archivo"""
        self.visit(self.tree)
        self._find_unused_imports()
        self._find_unused_variables()
        self._find_dead_code()
        self._find_complexity_issues()

        return dict(self.issues)

    def visit_Import(self, node: ast.Import) -> None:
        """Visitar nodos de import"""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name.split('.')[0]
            self.imported_names.add(name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visitar nodos de import from"""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imported_names.add(name)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visitar definiciones de función"""
        self.function_defs.add(node.name)
        self.defined_names.add(node.name)

        # Verificar complejidad
        if len(self._get_function_lines(node)) > 50:
            self.issues['long_functions'].append({
                'name': node.name,
                'line': node.lineno,
                'lines': len(self._get_function_lines(node))
            })

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visitar definiciones de clase"""
        self.class_defs.add(node.name)
        self.defined_names.add(node.name)

    def visit_Name(self, node: ast.Name) -> None:
        """Visitar usos de nombres"""
        if isinstance(node.ctx, (ast.Load, ast.AugLoad)):
            self.used_names.add(node.id)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visitar asignaciones"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.defined_names.add(target.id)

    def _find_unused_imports(self) -> None:
        """Encontrar imports no utilizados"""
        for name in self.imported_names:
            if name not in self.used_names and name != '*':
                # Verificar si es un import estándar que podría usarse indirectamente
                if not self._is_standard_import_usage(name):
                    self.issues['unused_imports'].append({
                        'name': name,
                        'line': self._find_import_line(name)
                    })

    def _find_unused_variables(self) -> None:
        """Encontrar variables no utilizadas"""
        for name in self.defined_names:
            if name not in self.used_names and not name.startswith('_'):
                # Excluir funciones y clases
                if name not in self.function_defs and name not in self.class_defs:
                    self.issues['unused_variables'].append({
                        'name': name,
                        'line': self._find_definition_line(name)
                    })

    def _find_dead_code(self) -> None:
        """Encontrar código muerto o comentado"""
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()

            # Código comentado largo
            if stripped.startswith('#') and len(stripped) > 50:
                self.issues['dead_code'].append({
                    'line': i,
                    'message': f"Código comentado largo: {stripped[:50]}..."
                })

            # TODO/FIXME comments  # REVIEW: Consider implementing  # REVIEW: Consider implementing
            if 'TODO' in stripped.upper() or 'FIXME' in stripped.upper():  # REVIEW: Consider implementing  # REVIEW: Consider implementing
                self.issues['dead_code'].append({
                    'line': i,
                    'message': f"Comentario TODO/FIXME: {stripped}"  # REVIEW: Consider implementing  # REVIEW: Consider implementing
                })

    def _find_complexity_issues(self) -> None:
        """Encontrar issues de complejidad"""
        # Números mágicos
        magic_pattern = r'\b\d{2,}\b'  # Números de 2+ dígitos
        for i, line in enumerate(self.lines, 1):
            if re.search(magic_pattern, line):
                # Excluir casos comunes
                if not any(exclude in line for exclude in ['import', 'from', '0', '1', '2']):
                    self.issues['magic_numbers'].append({
                        'line': i,
                        'message': f"Número mágico: {line.strip()}"
                    })

    def _is_standard_import_usage(self, name: str) -> bool:
        """Verificar si un import estándar se usa indirectamente"""
        standard_libs = {'os', 'sys', 're', 'json', 'datetime', 'pathlib', 'typing'}
        return name in standard_libs

    def _find_import_line(self, name: str) -> int:
        """Encontrar línea donde se importa un nombre"""
        for i, line in enumerate(self.lines, 1):
            if f'import {name}' in line or f'from {name}' in line:
                return i
        return 0

    def _find_definition_line(self, name: str) -> int:
        """Encontrar línea donde se define un nombre"""
        for i, line in enumerate(self.lines, 1):
            if f'{name} =' in line or f'def {name}' in line or f'class {name}' in line:
                return i
        return 0

    def _get_function_lines(self, node: ast.FunctionDef) -> List[str]:
        """Obtener líneas de una función"""
        if hasattr(node, 'end_lineno') and node.end_lineno:
            return self.lines[node.lineno-1:node.end_lineno]
        return []

def main():
    """Función principal"""
    project_dir = Path(__file__).parent

    print("🔬 INICIANDO ANÁLISIS AVANZADO DE CÓDIGO OBSOLETO")
    print(f"📁 Proyecto: {project_dir}")
    print("-" * REPORT_WIDTH)

    analyzer = CodeAnalyzer(project_dir)
    analyzer.find_python_files()
    analyzer.analyze_all_files()
    analyzer.generate_report()

    print("\n✅ Análisis completado!")

if __name__ == "__main__":
    main()