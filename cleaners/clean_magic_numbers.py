#!/usr/bin/env python3
"""
Script para limpiar números mágicos automáticamente
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

class MagicNumberCleaner:
    """Limpiador de números mágicos"""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.backup_dir = project_dir / "backup_magic_numbers"
        self.backup_dir.mkdir(exist_ok=True)

        # Definir constantes para números mágicos comunes
        self.constants = {
            'REDIS_DEFAULT_PORT': 'REDIS_DEFAULT_PORT',
            'DEFAULT_QUALITY_SCORE': 'DEFAULT_QUALITY_SCORE',
            'DEFAULT_ESTIMATED_DURATION': 'DEFAULT_ESTIMATED_DURATION',
            'REPORT_WIDTH': 'REPORT_WIDTH',
            'FORUM_ID': 'FORUM_ID',
            'MIN_TITLE_LENGTH': 'MIN_TITLE_LENGTH',
            'MIN_BODY_LENGTH': 'MIN_BODY_LENGTH',
            '100': 'MAX_COMMENT_LENGTH',
            'DEFAULT_TOKEN_LIMIT': 'DEFAULT_TOKEN_LIMIT',
            '1': 'DEFAULT_TEMPERATURE',
            'DEFAULT_TOP_P': 'DEFAULT_TOP_P'
        }

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

    def should_replace_magic_number(self, number: str, context: str) -> bool:
        """Determinar si un número mágico debe ser reemplazado"""
        # No reemplazar en URLs
        if 'http' in context.lower() or 'url' in context.lower():
            return False

        # No reemplazar en imports o nombres de módulos
        if 'import' in context or 'from ' in context:
            return False

        # No reemplazar en comentarios
        if context.strip().startswith('#'):
            return False

        # No reemplazar números muy comunes que podrían ser legítimos
        if number in ['0', '1', '2', '10', '100', '1000']:
            return False

        return True

    def add_constants_to_file(self, content: str, constants_needed: List[str]) -> str:
        """Agregar constantes necesarias al inicio del archivo"""
        lines = content.splitlines()

        # Encontrar dónde insertar las constantes (después de imports)
        insert_index = 0
        in_docstring = False
        in_imports = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Detectar docstring
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = not in_docstring
                continue

            # Saltar docstring
            if in_docstring:
                continue

            # Detectar imports
            if stripped.startswith(('import ', 'from ')) or in_imports:
                in_imports = True
                if stripped == '' and in_imports:
                    # Fin de los imports
                    insert_index = i + 1
                    break
            elif stripped and not in_imports:
                # Fin de la sección de imports/docstring
                insert_index = i
                break

        # Agregar constantes
        constants_to_add = []
        for const_name in constants_needed:
            if const_name in self.constants:
                value = list(self.constants.keys())[list(self.constants.values()).index(const_name)]
                constants_to_add.append(f"{const_name} = {value}")

        if constants_to_add:
            constants_block = "\n# Constants\n" + "\n".join(constants_to_add) + "\n\n"
            lines.insert(insert_index, constants_block)

        return "\n".join(lines)

    def clean_file(self, filepath: Path) -> Dict[str, int]:
        """Limpiar números mágicos en un archivo"""
        print(f"🔢 Procesando: {filepath.name}")

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes = {'magic_numbers_replaced': 0, 'constants_added': 0}
        constants_needed = []

        # Procesar cada número mágico
        for magic_num, const_name in self.constants.items():
            if magic_num in content:
                # Crear patrón que evite reemplazos en contextos no deseados
                pattern = r'(?<![\w./:])' + re.escape(magic_num) + r'(?![\w./:])'

                # Verificar contexto antes de reemplazar
                lines = content.splitlines()
                new_lines = []

                for line in lines:
                    if magic_num in line and self.should_replace_magic_number(magic_num, line):
                        # Reemplazar el número mágico
                        new_line = re.sub(pattern, const_name, line)
                        new_lines.append(new_line)

                        if const_name not in constants_needed:
                            constants_needed.append(const_name)
                            changes['constants_added'] += 1
                        changes['magic_numbers_replaced'] += 1
                    else:
                        new_lines.append(line)

                content = "\n".join(new_lines)

        # Agregar constantes si se hicieron reemplazos
        if constants_needed:
            content = self.add_constants_to_file(content, constants_needed)

        # Solo escribir si hubo cambios
        if content != original_content:
            self.create_backup(filepath)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ Limpiado: {filepath.name}")
        else:
            print(f"  ℹ️  Sin cambios: {filepath.name}")

        return changes

    def clean_all_files(self) -> None:
        """Limpiar todos los archivos del proyecto"""
        project_files = self.find_project_files()

        print(f"🔢 Iniciando limpieza de números mágicos en {len(project_files)} archivos...")
        print(f"📁 Backups guardados en: {self.backup_dir}")

        total_changes = {'magic_numbers_replaced': 0, 'constants_added': 0}

        for filepath in project_files:
            changes = self.clean_file(filepath)
            for key, value in changes.items():
                total_changes[key] += value

        # Reporte final
        print("\n" + "="*60)
        print("📊 REPORTE DE LIMPIEZA DE NÚMEROS MÁGICOS")
        print("="*60)

        if total_changes['magic_numbers_replaced'] > 0:
            print(f"✅ Números mágicos reemplazados: {total_changes['magic_numbers_replaced']}")
            print(f"✅ Constantes agregadas: {total_changes['constants_added']}")
            print(f"\n🔄 Backups disponibles en: {self.backup_dir}")
        else:
            print("ℹ️  No se encontraron números mágicos para reemplazar")

        print("\n💡 Constantes definidas:")
        for num, const in self.constants.items():
            print(f"  {const} = {num}")

def main():
    """Función principal"""
    project_dir = Path(__file__).parent

    print("🔢 INICIANDO LIMPIEZA DE NÚMEROS MÁGICOS")
    print(f"📁 Proyecto: {project_dir}")
    print("-" * 60)

    # Confirmar antes de proceder
    response = input("⚠️  Esta acción modificará archivos. ¿Continuar? (y/N): ")
    if response.lower() != 'y':
        print("❌ Limpieza cancelada")
        return

    cleaner = MagicNumberCleaner(project_dir)
    cleaner.clean_all_files()

    print("\n✅ Limpieza de números mágicos completada!")

if __name__ == "__main__":
    main()