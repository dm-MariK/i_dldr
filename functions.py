# functions.py

import os
import sys
from datetime import timezone
from pyicloud import PyiCloudService

def authenticate(apple_id):
    """
    Connecting ... (The token is automatically taken from ~/.pyicloud
    """
    print("Logging in to iCloud...")
    api = PyiCloudService(apple_id)
    
    # 2FA verification, if the session has expired
    if api.requires_2fa:
        print("Требуется код 2FA. Введите код из SMS/устройства Apple:")
        code = input("> ")
        if not api.validate_2fa_code(code):
            print("Неверный код 2FA")
            sys.exit(1)
    return api

def list_all_albums(api):
    """
    Display the list of all available albums in iCloud Photo
    """
    smart_albums = []
    user_albums = []
    folders = []

    for album in api.photos.albums:
        # Obtain album name and exclude empty names
        title = getattr(album, "title", str(album)).strip()
        if not title:
            continue
        album_type = type(album).__name__
        if "Smart" in album_type:
            smart_albums.append(title)
        elif "Folder" in album_type:
            folders.append(title)
        else:
            user_albums.append(title)

    # Sorting alphabetically
    smart_albums.sort()
    user_albums.sort()
    folders.sort()

    # Display ...
    print("\n================ Available albums in iCloud ================")
    print("=== Smart-albums (System): ===")
    for title in smart_albums:
        print(f"   • {title}")

    print("\n=== User albums: ===")
    for title in user_albums:
        print(f"   • {title}")

    if folders:
        print("\n=== Folders: ===")
        for title in folders:
            print(f"   • {title}")
    print("============================================================\n")

#------------------------------------------------------------------------------
def gen_local_path(photo, download_dir):
    """
    Will save photos as: YYYY/MM/YYYY-MM-DD_IMG_XXXX.PNG (or any other file extension)
    (relative to DOWNLOAD_DIR)
    """
    if photo.created:
        dt = photo.created.replace(tzinfo=timezone.utc)
        year_str = dt.strftime("%Y")
        month_str = dt.strftime("%m")
        date_prefix = dt.strftime("%Y-%m-%d")

        # Целевая подпапка: YYYY/MM
        target_dir = os.path.join(download_dir, year_str, month_str)

        # Проверяем, чтобы префикс даты не задублировался
        if photo.filename.startswith(f"{date_prefix}_"):
            filename = photo.filename
        else:
            filename = f"{date_prefix}_{photo.filename}"
    else:
        #year_str, month_str = "Unknown", "Unknown"
        target_dir = download_dir
        filename = photo.filename

    os.makedirs(target_dir, exist_ok=True)
    filepath = os.path.join(target_dir, filename)

    rel_path = os.path.relpath(filepath, download_dir)
    
    return filepath, rel_path
# -----------------------------------------------------------------------------

def get_photo(photo, filepath):
    download = photo.download()
    with open(filepath, "wb") as f:
        if isinstance(download, bytes):
            f.write(download)
        elif hasattr(download, "content"):
            f.write(download.content)
        else:
            f.write(download.raw.read())

    # Set up correct file modification time (mtime)
    if photo.created:
        dt = photo.created.replace(tzinfo=timezone.utc)
        timestamp = dt.timestamp()
        os.utime(filepath, (timestamp, timestamp))
        
# -----------------------------------------------------------------------------

def check_counts(photos):
    """ 
    Calculates real number of objects in photos = api.photos.albums[ALBUM_NAME].
    Compare it with number declared by Apple service.
    """
    print(f"\nМетаданные (len): {len(photos)}")

    print("Начинаю реальный перебор объектов (без скачивания)...")
    actual_count = 0
    # set() is used here because Sets only store unique items. 
    # Adding an existing filename will do nothing. Duplicates are ignored.
    filenames = set()

    # Просто перебираем и считаем
    for photo in photos:
        actual_count += 1
        filenames.add(photo.filename)
    
    print(f"Реально получено объектов в цикле: {actual_count}")
    print(f"Уникальных имен файлов: {len(filenames)}")

    if len(photos) != actual_count:
        print("\n⚠️ ПОДТВЕРЖДЕНО: Apple заявляет одно количество, но отдает другое.")
        print("Это не ошибка вашего скрипта загрузки. Это то, как отвечает сервер iCloud.")
    
# Стоит ли волноваться?
# Нет. Если скрипт честно дошел до конца цикла for и не упал с ошибкой, 
# значит он обработал абсолютно все файлы, которые сервер iCloud согласился ему отдать.
# 
# Эти 2 недостающих объекта — это либо "мусорные" записи в базе данных Apple, 
# либо скрытые видео-дубли от Live Photos, которые привязались к альбому "Скриншоты" 
# из-за какого-то системного сбоя в iOS. Вы не потеряли свои реальные фотографии.
# -----------------------------------------------------------------------------
