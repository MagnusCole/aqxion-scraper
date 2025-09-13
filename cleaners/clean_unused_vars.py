#!/usr/bin/env python3
"""
Script para limpiar variables no utilizadas automáticamente
"""

import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

class UnusedVariableCleaner:
    """Limpiador de variables no utilizadas"""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.backup_dir = project_dir / "backup_unused_vars"
        self.backup_dir.mkdir(exist_ok=True)

    def find_project_files(self) -> List[Path]:
        """Encontrar archivos Python del proyecto"""
        exclude_dirs = {'venv', '.venv', 'env', '__pycache__', 'pandas', 'numpy'}
        project_files = []

        for filepath in self.project_dir.rglob('*.py'):
            if not any(part in exclude_dirs for part in filepath.parts):
                project_files.append(filepath)

        return project_files

    def create_backup(self, filepath: Path) -> Path:
        """Crear backup del archivo"""
        backup_path = self.backup_dir / f"{filepath.name}.backup"
        with open(filepath, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        return backup_path

    def analyze_file_variables(self, filepath: Path) -> Tuple[Set[str], Set[str], List[Tuple[str, int]]]:
        """Analizar variables definidas y utilizadas en un archivo"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(filepath))

            defined_vars = set()
            used_vars = set()
            var_locations = []

            class VariableAnalyzer(ast.NodeVisitor):
                def __init__(self):
                    self.defined = set()
                    self.used = set()
                    self.locations = []

                def visit_Assign(self, node):
                    """Visitar asignaciones"""
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self.defined.add(target.id)
                            self.locations.append((target.id, node.lineno))

                def visit_Name(self, node):
                    """Visitar usos de nombres"""
                    if isinstance(node.ctx, (ast.Load, ast.AugLoad)):
                        self.used.add(node.id)

                def visit_FunctionDef(self, node):
                    """Visitar definiciones de función"""
                    # No contar parámetros como variables locales no utilizadas
                    # (aunque técnicamente no se usen en el cuerpo)
                    for arg in node.args.args:
                        self.used.add(arg.arg)

                def visit_AsyncFunctionDef(self, node):
                    """Visitar definiciones de función async"""
                    for arg in node.args.args:
                        self.used.add(arg.arg)

            analyzer = VariableAnalyzer()
            analyzer.visit(tree)

            return analyzer.defined, analyzer.used, analyzer.locations

        except SyntaxError:
            return set(), set(), []

    def should_remove_variable(self, var_name: str, defined_vars: Set[str], used_vars: Set[str]) -> bool:
        """Determinar si una variable debe ser removida"""
        # No remover si se usa
        if var_name in used_vars:
            return False

        # No remover variables que empiezan con underscore (convención de "no usado")
        if var_name.startswith('_'):
            return False

        # No remover variables comunes que podrían tener uso implícito
        common_vars = {'self', 'cls', 'args', 'kwargs', 'settings', 'config'}
        if var_name in common_vars:
            return False

        return True

    def find_variable_line(self, content: str, var_name: str, line_number: int) -> Tuple[str, int]:
        """Encontrar la línea completa donde se define una variable"""
        lines = content.splitlines()
        if 1 <= line_number <= len(lines):
            line = lines[line_number - 1]
            # Verificar que la variable esté en esta línea
            if f'{var_name} =' in line or f'{var_name}=' in line:
                return line, line_number
        return "", 0

    def remove_variable_assignment(self, content: str, var_name: str, line_number: int) -> str:
        """Remover la asignación de una variable no utilizada"""
        lines = content.splitlines()
        if 1 <= line_number <= len(lines):
            line = lines[line_number - 1]

            # Solo remover si es una asignación simple
            if re.match(rf'^\s*{re.escape(var_name)}\s*=', line):
                # Verificar que no sea parte de una estructura más compleja
                stripped = line.strip()
                if ',' not in stripped and '(' not in stripped and '[' not in stripped:
                    # Remover la línea
                    lines.pop(line_number - 1)
                    return "\n".join(lines)

        return content

    def clean_file(self, filepath: Path) -> Dict[str, int]:
        """Limpiar variables no utilizadas en un archivo"""
        print(f"🧹 Procesando variables: {filepath.name}")

        defined_vars, used_vars, var_locations = self.analyze_file_variables(filepath)

        if not defined_vars:
            print(f"  ℹ️  No se encontraron variables para analizar: {filepath.name}")
            return {'variables_removed': 0}

        # Encontrar variables no utilizadas
        unused_vars = []
        for var_name in defined_vars:
            if self.should_remove_variable(var_name, defined_vars, used_vars):
                unused_vars.append(var_name)

        if not unused_vars:
            print(f"  ℹ️  No se encontraron variables no utilizadas: {filepath.name}")
            return {'variables_removed': 0}

        # Leer contenido original
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        removed_count = 0

        # Procesar cada variable no utilizada
        for var_name in unused_vars:
            # Encontrar todas las ubicaciones de esta variable
            var_locations_for_name = [(name, line) for name, line in var_locations if name == var_name]

            for var_name_loc, line_number in var_locations_for_name:
                # Verificar que aún no se haya removido
                current_lines = content.splitlines()
                if line_number <= len(current_lines):
                    line = current_lines[line_number - 1]
                    if f'{var_name} =' in line or f'{var_name}=' in line:
                        content = self.remove_variable_assignment(content, var_name, line_number)
                        removed_count += 1
                        break  # Solo remover la primera ocurrencia

        # Solo escribir si hubo cambios
        if content != original_content and removed_count > 0:
            self.create_backup(filepath)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ Variables limpiadas: {filepath.name} ({removed_count} removidas)")
        else:
            print(f"  ℹ️  Sin cambios en variables: {filepath.name}")

        return {'variables_removed': removed_count}

    def clean_all_files(self) -> None:
        """Limpiar variables no utilizadas en todos los archivos"""
        project_files = self.find_project_files()

        print(f"🧹 Iniciando limpieza de variables no utilizadas en {len(project_files)} archivos...")
        print(f"📁 Backups guardados en: {self.backup_dir}")

        total_changes = {'variables_removed': 0}

        for filepath in project_files:
            changes = self.clean_file(filepath)
            total_changes['variables_removed'] += changes['variables_removed']

        # Reporte final
        print("\n" + "="*60)
        print("📊 REPORTE DE LIMPIEZA DE VARIABLES NO UTILIZADAS")
        print("="*60)

        if total_changes['variables_removed'] > 0:
            print(f"✅ Variables no utilizadas removidas: {total_changes['variables_removed']}")
            print(f"\n🔄 Backups disponibles en: {self.backup_dir}")
            print("\n💡 Variables removidas incluyen:")
            print("  - Asignaciones simples no referenciadas")
            print("  - Variables locales sin uso")
            print("  - Excluyendo variables con underscore (_) y parámetros")
        else:
            print("ℹ️  No se encontraron variables no utilizadas para remover")
            print("💡 Esto puede deberse a:")
            print("  - Variables ya fueron limpiadas anteriormente")
            print("  - Variables tienen uso implícito o indirecto")
            print("  - Variables están protegidas (empiezan con _)")

def main():
    """Función principal"""
    project_dir = Path(__file__).parent

    print("🧹 INICIANDO LIMPIEZA DE VARIABLES NO UTILIZADAS")
    print(f"📁 Proyecto: {project_dir}")
    print("-" * 60)

    # Confirmar antes de proceder
    response = input("⚠️  Esta acción modificará archivos. ¿Continuar? (y/N): ")
    if response.lower() != 'y':
        print("❌ Limpieza cancelada")
        return

    cleaner = UnusedVariableCleaner(project_dir)
    cleaner.clean_all_files()

    print("\n✅ Limpieza de variables no utilizadas completada!")

if __name__ == "__main__":
    main()
