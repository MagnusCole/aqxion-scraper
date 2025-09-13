#!/usr/bin/env python3
"""
Script automático para limpiar código obsoleto identificado
"""

import os
import re
import ast
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple, Any
from collections import defaultdict

class CodeCleaner:
    """Limpiador automático de código obsoleto"""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.backup_dir = project_dir / "backup_before_cleanup"
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, filepath: Path) -> Path:
        """Crear backup del archivo antes de modificarlo"""
        backup_path = self.backup_dir / f"{filepath.name}.backup"
        with open(filepath, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        return backup_path

    def clean_file(self, filepath: Path) -> Dict[str, int]:
        """Limpiar un archivo específico"""
        print(f"🧹 Limpiando: {filepath.name}")

        # Crear backup
        backup_path = self.create_backup(filepath)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()

            cleaned_content = original_content
            changes = {}

            # 1. Remover imports no utilizados
            cleaned_content, import_changes = self.remove_unused_imports(cleaned_content)
            changes['imports_removed'] = import_changes

            # 2. Remover variables no utilizadas
            cleaned_content, var_changes = self.remove_unused_variables(cleaned_content)
            changes['variables_removed'] = var_changes

            # 3. Limpiar código comentado
            cleaned_content, comment_changes = self.clean_commented_code(cleaned_content)
            changes['comments_cleaned'] = comment_changes

            # 4. Reemplazar números mágicos
            cleaned_content, magic_changes = self.replace_magic_numbers(cleaned_content)
            changes['magic_numbers_fixed'] = magic_changes

            # Solo escribir si hubo cambios
            if cleaned_content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                print(f"  ✅ Archivo limpiado: {filepath.name}")
            else:
                print(f"  ℹ️  No se encontraron cambios en: {filepath.name}")

            return changes

        except Exception as e:
            print(f"  ❌ Error limpiando {filepath.name}: {e}")
            # Restaurar backup en caso de error
            with open(backup_path, 'r', encoding='utf-8') as src:
                with open(filepath, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            return {}

    def remove_unused_imports(self, content: str) -> Tuple[str, int]:
        """Remover imports no utilizados"""
        lines = content.splitlines()
        tree = ast.parse(content)

        # Encontrar imports utilizados
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Load, ast.AugLoad)):
                used_names.add(node.id)

        # Procesar líneas de import
        cleaned_lines = []
        removed_count = 0

        for line in lines:
            stripped = line.strip()

            # Import statements
            if stripped.startswith(('import ', 'from ')):
                # Extraer nombres importados
                imported_names = self.extract_imported_names(stripped)

                # Verificar si se usan
                should_remove = True
                for name in imported_names:
                    if name in used_names or self.is_standard_lib(name):
                        should_remove = False
                        break

                if should_remove:
                    removed_count += 1
                    continue  # Saltar esta línea

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines), removed_count

    def remove_unused_variables(self, content: str) -> Tuple[str, int]:
        """Remover variables no utilizadas (simplificado)"""
        # Esta es una versión simplificada - en producción usaríamos un analizador más sofisticado
        lines = content.splitlines()
        cleaned_lines = []
        removed_count = 0

        # Patrón para encontrar asignaciones simples no utilizadas
        # Nota: Esta es una aproximación simplificada
        for line in lines:
            # Mantener todas las líneas por ahora (requiere análisis AST más complejo)
            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines), removed_count

    def clean_commented_code(self, content: str) -> Tuple[str, int]:
        """Limpiar código comentado largo y TODOs antiguos"""  # REVIEW: Consider implementing  # REVIEW: Consider implementing
        lines = content.splitlines()
        cleaned_lines = []
        removed_count = 0

        for line in lines:
            stripped = line.strip()

            # Remover comentarios largos (>100 caracteres)
            if stripped.startswith('#') and len(stripped) > 100:
                removed_count += 1
                continue

            # Mantener TODOs importantes pero marcar para revisión  # REVIEW: Consider implementing  # REVIEW: Consider implementing
            if 'TODO' in stripped.upper() or 'FIXME' in stripped.upper():  # REVIEW: Consider implementing  # REVIEW: Consider implementing
                # Agregar comentario de revisión
                cleaned_lines.append(line + "  # REVIEW: Consider implementing")
                continue

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines), removed_count

    def replace_magic_numbers(self, content: str) -> Tuple[str, int]:
        """Reemplazar números mágicos con constantes"""
        # Definir constantes comunes
        constants = {
            'REDIS_DEFAULT_PORT': 'REDIS_DEFAULT_PORT',
            'DEFAULT_QUALITY_SCORE': 'DEFAULT_QUALITY_SCORE',
            'DEFAULT_ESTIMATED_DURATION': 'DEFAULT_ESTIMATED_DURATION',
            'REPORT_WIDTH': 'REPORT_WIDTH',
            'FORUM_ID': 'FORUM_ID'  # Para el caso específico encontrado
        }

        replaced_count = 0
        for magic_num, constant in constants.items():
            if magic_num in content:
                # Solo reemplazar si no está en URLs o imports
                pattern = r'(?<![\w./:])' + re.escape(magic_num) + r'(?![\w./:])'
                content = re.sub(pattern, constant, content)
                replaced_count += 1

        return content, replaced_count

    def extract_imported_names(self, import_line: str) -> List[str]:
        """Extraer nombres de una línea de import"""
        names = []

        if import_line.startswith('import '):
            # import module1, module2
            parts = import_line[7:].split(',')
            for part in parts:
                name = part.strip().split('.')[0]
                names.append(name)
        elif import_line.startswith('from '):
            # from module import name1, name2
            if ' import ' in import_line:
                after_import = import_line.split(' import ')[1]
                parts = after_import.split(',')
                for part in parts:
                    name = part.strip().split(' as ')[0].strip()
                    names.append(name)

        return names

    def is_standard_lib(self, name: str) -> bool:
        """Verificar si es una librería estándar"""
        standard_libs = {
            'os', 'sys', 're', 'json', 'datetime', 'pathlib', 'typing',
            'asyncio', 'threading', 'subprocess', 'collections', 'itertools',
            'functools', 'operator', 'time', 'random', 'math', 'statistics'
        }
        return name in standard_libs

    def clean_all_files(self) -> None:
        """Limpiar todos los archivos Python del proyecto"""  # REVIEW: Consider implementing  # REVIEW: Consider implementing
        python_files = []
        exclude_patterns = {'__pycache__', 'backup_before_cleanup'}

        for filepath in self.project_dir.rglob('*.py'):
            if not any(pattern in str(filepath) for pattern in exclude_patterns):
                python_files.append(filepath)

        print(f"🧹 Iniciando limpieza de {len(python_files)} archivos...")
        print(f"📁 Backups guardados en: {self.backup_dir}")

        total_changes = defaultdict(int)

        for filepath in python_files:
            changes = self.clean_file(filepath)
            for key, value in changes.items():
                total_changes[key] += value

        # Reporte final
        print("\n" + "="*60)
        print("📊 REPORTE DE LIMPIEZA COMPLETADA")
        print("="*60)

        for change_type, count in total_changes.items():
            if count > 0:
                print(f"✅ {change_type.replace('_', ' ').title()}: {count}")

        if not total_changes:
            print("ℹ️  No se realizaron cambios automáticos")
            print("💡 Recomendación: Revisar manualmente los issues reportados")

        print(f"\n🔄 Backups disponibles en: {self.backup_dir}")
        print("💡 Para restaurar: copiar archivos .backup a sus ubicaciones originales")

def main():
    """Función principal"""
    project_dir = Path(__file__).parent

    print("🧹 INICIANDO LIMPIEZA AUTOMÁTICA DE CÓDIGO OBSOLETO")
    print(f"📁 Proyecto: {project_dir}")
    print("-" * 60)

    # Confirmar antes de proceder
    response = input("⚠️  Esta acción modificará archivos. ¿Continuar? (y/N): ")
    if response.lower() != 'y':
        print("❌ Limpieza cancelada")
        return

    cleaner = CodeCleaner(project_dir)
    cleaner.clean_all_files()

    print("\n✅ Limpieza completada!")
    print("🔍 Recomendación: Ejecutar análisis nuevamente para verificar mejoras")

if __name__ == "__main__":
    main()