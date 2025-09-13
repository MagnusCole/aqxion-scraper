#!/usr/bin/env python3
"""
Clean Empty Files - Limpia archivos vacíos del proyecto

Este script identifica y elimina todos los archivos vacíos (0 bytes)
en el proyecto, manteniendo la estructura de directorios limpia.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple

# Archivos que NUNCA deben eliminarse, incluso si están vacíos
PROTECTED_FILES = {
    '__init__.py',      # Archivos de inicialización de módulos
    '.gitkeep',         # Marcadores de directorios Git
    '.gitignore',       # Configuración Git (aunque no debería estar vacío)
    'README.md',        # Documentación principal
    'requirements.txt', # Dependencias (aunque no debería estar vacío)
    '.env',            # Variables de entorno
}

# Extensiones que revisar (para evitar eliminar archivos binarios importantes)
ALLOWED_EXTENSIONS = {
    '.py', '.md', '.txt', '.json', '.yaml', '.yml', '.toml',
    '.csv', '.log', '.sh', '.ps1', '.bat', '.ini', '.cfg',
    '.xml', '.html', '.css', '.js', '.ts', '.sql'
}

class EmptyFilesCleaner:
    """Limpiador de archivos vacíos"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.empty_files: List[Path] = []
        self.protected_files: List[Path] = []
        self.errors: List[Tuple[Path, str]] = []

    def is_empty_file(self, file_path: Path) -> bool:
        """Verifica si un archivo está vacío"""
        try:
            return file_path.stat().st_size == 0
        except OSError as e:
            self.errors.append((file_path, f"Error al verificar tamaño: {e}"))
            return False

    def should_delete_file(self, file_path: Path) -> bool:
        """Determina si un archivo debe eliminarse"""
        # No eliminar archivos protegidos
        if file_path.name in PROTECTED_FILES:
            return False

        # Solo eliminar archivos con extensiones permitidas
        if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            return False

        # Verificar si está vacío
        return self.is_empty_file(file_path)

    def scan_project(self) -> None:
        """Escanea todo el proyecto en busca de archivos vacíos"""
        print(f"🔍 Escaneando proyecto: {self.project_root}")

        for file_path in self.project_root.rglob('*'):
            if file_path.is_file():
                if file_path.name in PROTECTED_FILES:
                    self.protected_files.append(file_path)
                elif self.should_delete_file(file_path):
                    self.empty_files.append(file_path)

        print(f"📊 Archivos encontrados:")
        print(f"   • Vacíos candidatos: {len(self.empty_files)}")
        print(f"   • Protegidos: {len(self.protected_files)}")
        print(f"   • Errores: {len(self.errors)}")

    def show_protected_files(self) -> None:
        """Muestra archivos protegidos encontrados"""
        if self.protected_files:
            print(f"\n🛡️ Archivos protegidos (no se eliminarán):")
            for file_path in sorted(self.protected_files):
                relative_path = file_path.relative_to(self.project_root)
                print(f"   • {relative_path}")

    def show_empty_files(self) -> None:
        """Muestra archivos vacíos encontrados"""
        if self.empty_files:
            print(f"\n📁 Archivos vacíos encontrados:")
            for file_path in sorted(self.empty_files):
                relative_path = file_path.relative_to(self.project_root)
                print(f"   • {relative_path}")
        else:
            print(f"\n✅ No se encontraron archivos vacíos para eliminar")

    def delete_empty_files(self, dry_run: bool = True) -> int:
        """Elimina archivos vacíos encontrados"""
        if not self.empty_files:
            print(f"\n✅ No hay archivos para eliminar")
            return 0

        deleted_count = 0

        if dry_run:
            print(f"\n🔍 MODO PRUEBA - No se eliminarán archivos")
            print(f"   Para eliminar realmente, ejecuta con --delete")
        else:
            print(f"\n🗑️ Eliminando archivos vacíos...")

        for file_path in self.empty_files:
            relative_path = file_path.relative_to(self.project_root)

            if dry_run:
                print(f"   • [SIMULADO] {relative_path}")
                deleted_count += 1
            else:
                try:
                    file_path.unlink()
                    print(f"   ✅ Eliminado: {relative_path}")
                    deleted_count += 1
                except OSError as e:
                    print(f"   ❌ Error eliminando {relative_path}: {e}")
                    self.errors.append((file_path, f"Error al eliminar: {e}"))

        return deleted_count

    def show_errors(self) -> None:
        """Muestra errores encontrados"""
        if self.errors:
            print(f"\n❌ Errores encontrados:")
            for file_path, error in self.errors:
                relative_path = file_path.relative_to(self.project_root)
                print(f"   • {relative_path}: {error}")

def main():
    """Función principal"""
    print("🧹 CLEAN EMPTY FILES - Limpieza de archivos vacíos")
    print("=" * 60)

    # Determinar directorio raíz del proyecto
    script_dir = Path(__file__).parent

    # Buscar el directorio raíz del proyecto (donde están los archivos principales)
    project_root = script_dir
    max_levels = 3  # Máximo 3 niveles hacia arriba

    for _ in range(max_levels):
        if (project_root / 'requirements.txt').exists() or \
           (project_root / 'pyproject.toml').exists() or \
           (project_root / '.git').exists():
            break
        project_root = project_root.parent

    # Verificar si encontramos el directorio correcto
    if not ((project_root / 'requirements.txt').exists() or
            (project_root / 'pyproject.toml').exists() or
            (project_root / '.git').exists()):
        print(f"❌ No se encontró el directorio raíz del proyecto")
        print(f"   Ejecutando desde: {script_dir}")
        print(f"   Proyecto detectado: {project_root}")
        print(f"   Archivos encontrados en raíz:")
        for file in ['requirements.txt', 'pyproject.toml', '.git']:
            exists = (project_root / file).exists()
            print(f"     • {file}: {'✅' if exists else '❌'}")
        sys.exit(1)

    # Parsear argumentos
    import argparse
    parser = argparse.ArgumentParser(description='Limpia archivos vacíos del proyecto')
    parser.add_argument('--delete', action='store_true',
                       help='Eliminar archivos realmente (por defecto solo simula)')
    parser.add_argument('--quiet', action='store_true',
                       help='Modo silencioso, menos output')
    parser.add_argument('--path', type=str,
                       help='Ruta específica a escanear (por defecto: directorio del proyecto)')

    args = parser.parse_args()

    # Usar ruta específica si se proporciona
    if args.path:
        scan_path = Path(args.path)
        if not scan_path.exists():
            print(f"❌ Ruta no existe: {scan_path}")
            sys.exit(1)
    else:
        scan_path = project_root

    # Crear limpiador
    cleaner = EmptyFilesCleaner(scan_path)

    # Escanear proyecto
    cleaner.scan_project()

    if not args.quiet:
        # Mostrar resultados
        cleaner.show_protected_files()
        cleaner.show_empty_files()

    # Eliminar archivos
    deleted = cleaner.delete_empty_files(dry_run=not args.delete)

    # Mostrar errores
    if not args.quiet:
        cleaner.show_errors()

    # Resumen final
    print(f"\n📊 RESUMEN:")
    if args.delete:
        print(f"   ✅ Archivos eliminados: {deleted}")
    else:
        print(f"   🔍 Archivos que se eliminarían: {deleted}")
        print(f"   💡 Ejecuta con --delete para eliminar realmente")

    print(f"\n🎉 Limpieza completada!")

if __name__ == "__main__":
    main()
