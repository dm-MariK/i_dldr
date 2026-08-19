#!/usr/bin/env python3

import os
import re
import shutil
from datetime import datetime, timezone
import argparse

try:
    import config
except ModuleNotFoundError:
    print("❌ Ошибка: Файл 'config.py' не найден!")
    print("💡 Скопируйте 'config.example.py' в 'config.py' и заполните ваши данные.")
    sys.exit(1)
    
# Попытка импорта Pillow для EXIF
try:
    from PIL import Image

    HAS_PIL = True
except ImportError:
    HAS_PIL = False
# ---------------------------------------------------------------------

def get_args():
    parser = argparse.ArgumentParser(description='''
Вспомогательный скрипт к Загрузчику фото из iCloud (dldr.py).
Сортирует скачанные файлы по папкам и добавляет дату создания их именам,
используя метаданные. Приводит к формату: 
YYYY/MM/YYYY-MM-DD_<ORIG-FILE-NAME>.<ORIG-FILE-EXT>
'''
    )
    
    parser.add_argument("-d", "--dir", type=str, 
                        default=config.DOWNLOAD_DIR, 
                        help="Local directory with downloaded files.")
    return parser.parse_args()
# ---------------------------------------------------------------------

def get_file_date(filepath):
    """Извлекает дату создания из EXIF или fallback на mtime файла."""
    if HAS_PIL:
        try:
            with Image.open(filepath) as img:
                exif = img._getexif()
                if exif:
                    # 36867 - DateTimeOriginal, 306 - DateTime
                    date_str = exif.get(36867) or exif.get(306)
                    if date_str:
                        return datetime.strptime(
                            date_str, "%Y:%m:%d %H:%M:%S"
                        ).replace(tzinfo=timezone.utc)
        except Exception:
            pass

    # Если EXIF нет, берём время изменения файла (mtime), которое выставил icloudpd/скрипт
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime, tz=timezone.utc)
# ---------------------------------------------------------------------

def organize(download_dir):
    print(f"Начинаем сортировку файлов в: {download_dir}\n")

    moved_count = 0
    skipped_count = 0
    conflict_count = 0

    # Обходим все файлы (включая уже существующие подпапки)
    for root, dirs, files in os.walk(download_dir):
        for filename in files:
            # Игнорируем сам скрипт или скрытые файлы (.DS_Store и т.д.)
            if filename.startswith(".") or filename.endswith(".py"):
                continue

            current_filepath = os.path.join(root, filename)

            # Получаем дату
            dt = get_file_date(current_filepath)
            year_str = dt.strftime("%Y")
            month_str = dt.strftime("%m")
            date_prefix = dt.strftime("%Y-%m-%d")

            # Очищаем оригинальное имя от старых префиксов дат (если они уже были добавлены)
            clean_filename = re.sub(r"^\d{4}-\d{2}-\d{2}_", "", filename)

            # Новое имя с префиксом даты
            new_filename = f"{date_prefix}_{clean_filename}"

            # Целевой путь: YYYY/MM/YYYY-MM-DD_clean_filename
            target_dir = os.path.join(download_dir, year_str, month_str)
            target_filepath = os.path.join(target_dir, new_filename)

            # Если файл уже находится на своем месте с правильным именем
            if current_filepath == target_filepath:
                skipped_count += 1
                continue

            os.makedirs(target_dir, exist_ok=True)

            # Перемещение файла
            if os.path.exists(target_filepath) and current_filepath != target_filepath:
                print(
                    f"⚠ Внимание: целевой файл {new_filename} уже существует. Пропускаем дубликат: {current_filepath}"
                )
                conflict_count += 1
            else:
                shutil.move(current_filepath, target_filepath)
                rel_old = os.path.relpath(current_filepath, download_dir)
                rel_new = os.path.relpath(target_filepath, download_dir)
                print(f" * Перемещен: {rel_old} -> {rel_new}")
                moved_count += 1

    # Удаляем пустые старые подпапки (например, пустые папки дней YYYY/MM/DD)
    for root, dirs, files in os.walk(download_dir, topdown=False):
        for d in dirs:
            dir_path = os.path.join(root, d)
            if not os.listdir(dir_path):
                os.rmdir(dir_path)

    print(
        f"\n✅ Готово! "
        f"\n  * Перемещено и переименовано файлов: {moved_count}, "
        f"\n  * уже были на месте: {skipped_count}, "
        f"\n  * не перемещены вследствие конфликта имён: {conflict_count}."
    )
# ---------------------------------------------------------------------

if __name__ == "__main__":
    args = get_args()
    organize(args.dir)
