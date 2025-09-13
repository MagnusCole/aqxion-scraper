#!/usr/bin/env python3
"""
Script para limpiar archivos vacíos y obsoletos del proyecto Aqxion Scraper
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple

def is_empty_file(filepath: Path) -> bool:
    """Verificar si un archivo está vacío (0 bytes)"""
    try:
        return filepath.stat().st_size == 0
    except OSError:
        return False

def is_obsolete_file(filepath: Path) -> bool:
    """Determinar si un archivo es obsoleto basado en criterios"""
    filename = filepath.name.lower()

    # Archivos en directorios de cache
    if any(part in ['__pycache__', '.pytest_cache', '.mypy_cache', '.vscode', '.idea']
           for part in filepath.parts):
        return True

    # Archivos con extensiones temporales
    temp_extensions = ['.tmp', '.bak', '.orig', '.swp', '.swo', '~']
    if any(filename.endswith(ext) for ext in temp_extensions):
        return True

    # Archivos con nombres que indican obsolescencia
    obsolete_patterns = ['test_', '_old', '_backup', 'old_', 'backup_']
    if any(pattern in filename for pattern in obsolete_patterns):
        return True

    # Archivos de log antiguos (excepto logs actuales)
    if filename.endswith('.log') and 'logs' in filepath.parts:
        # Mantener logs recientes, eliminar logs antiguos
        try:
            # Si el archivo tiene más de 30 días, considerarlo obsoleto
            import time
            file_age_days = (time.time() - filepath.stat().st_mtime) / (24 * 3600)
            if file_age_days > 30:
                return True
        except:
            pass

    return False

def find_files_to_clean(root_dir: Path) -> Tuple[List[Path], List[Path]]:
    """Encontrar archivos vacíos y obsoletos"""
    empty_files = []
    obsolete_files = []

    # Archivos/directorios a excluir completamente
    exclude_dirs = {'.git', 'node_modules', 'venv', '.venv', 'env', '.env'}

    for filepath in root_dir.rglob('*'):
        # Saltar directorios excluidos
        if any(part in exclude_dirs for part in filepath.parts):
            continue

        # Solo procesar archivos
        if not filepath.is_file():
            continue

        # Verificar archivos vacíos
        if is_empty_file(filepath):
            empty_files.append(filepath)
            continue

        # Verificar archivos obsoletos
        if is_obsolete_file(filepath):
            obsolete_files.append(filepath)

    return empty_files, obsolete_files

def confirm_deletion(files: List[Path], category: str) -> bool:
    """Pedir confirmación antes de eliminar archivos"""
    if not files:
        return True

    print(f"\n🔍 {category.upper()}:")
    for file in files[:10]:  # Mostrar máximo 10 archivos
        print(f"  - {file}")

    if len(files) > 10:
        print(f"  ... y {len(files) - 10} archivos más")

    response = input(f"\n¿Eliminar {len(files)} {category.lower()}? (y/N): ").strip().lower()
    return response in ['y', 'yes', 's', 'si']

def delete_files(files: List[Path], category: str) -> int:
    """Eliminar archivos y retornar contador"""
    deleted = 0
    for filepath in files:
        try:
            filepath.unlink()
            deleted += 1
        except Exception as e:
            print(f"❌ Error eliminando {filepath}: {e}")

    if deleted > 0:
        print(f"✅ Eliminados {deleted} archivos {category.lower()}")

    return deleted

def main():
    """Función principal"""
    # Directorio del proyecto
    project_dir = Path(__file__).parent

    print("🧹 Iniciando limpieza del proyecto Aqxion Scraper")
    print(f"📁 Directorio: {project_dir}")

    # Encontrar archivos a limpiar
    empty_files, obsolete_files = find_files_to_clean(project_dir)

    total_candidates = len(empty_files) + len(obsolete_files)
    if total_candidates == 0:
        print("✨ No se encontraron archivos para limpiar")
        return

    print(f"\n📊 Encontrados {total_candidates} archivos candidatos:")
    print(f"  - {len(empty_files)} archivos vacíos")
    print(f"  - {len(obsolete_files)} archivos obsoletos")

    # Confirmar y eliminar archivos vacíos
    if confirm_deletion(empty_files, "archivos vacíos"):
        delete_files(empty_files, "vacíos")

    # Confirmar y eliminar archivos obsoletos
    if confirm_deletion(obsolete_files, "archivos obsoletos"):
        delete_files(obsolete_files, "obsoletos")

    print("\n🎉 Limpieza completada!")

if __name__ == "__main__":
    main()