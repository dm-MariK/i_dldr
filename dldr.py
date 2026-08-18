#!/usr/bin/env python3
import os
import sys

# 1. Безопасно импортируем локальный конфиг
try:
    import config
except ModuleNotFoundError:
    print("❌ Ошибка: Файл 'config.py' не найден!")
    print("💡 Скопируйте 'config.example.py' в 'config.py' и заполните ваши данные.")
    sys.exit(1)

# 2. Проверяем интерпретатор на основе пути из config.py
TARGET_PYTHON = getattr(config, "TARGET_PYTHON", None)

if TARGET_PYTHON and sys.executable != TARGET_PYTHON:
    if not os.path.exists(TARGET_PYTHON):
        print(f"❌ Ошибка: Интерпретатор не найден по пути: {TARGET_PYTHON}")
        sys.exit(1)
        
    # Заменяем процесс на Python из Conda
    os.execv(TARGET_PYTHON, [TARGET_PYTHON] + sys.argv)

# =====================================================================
# 3. ТЕПЕРЬ МЫ 100% ВНУТРИ CONDA-ОКРУЖЕНИЯ
# Только здесь начинаем импортировать тяжелые модули и functions.py
# =====================================================================

import functions

import argparse
import logging
import socket

# ---------------------------------------------------------------------
def parse_timeout(value):
    """Convert string to int or None"""
    if value.lower() == 'none':
        return None
    try:
        val = int(value)
        if val <= 0: # 0 or negative vals also mean infinite time-out, thus convert it to None
            #raise argparse.ArgumentTypeError("Тайм-аут должен быть больше нуля")
            return None
        return val
    except ValueError:
        raise argparse.ArgumentTypeError(f"Ожидается целое число или 'None', получено: '{value}'")
# ---------------------------------------------------------------------

def get_args():
    parser = argparse.ArgumentParser(description="Загрузчик фото из iCloud")
    
    # default=config.APPLE_ID -- to use default value from config.py
    parser.add_argument("-u", "--user", type=str, 
                        default=config.APPLE_ID, 
                        help="Apple ID (email).")
    
    parser.add_argument("-a", "--album", type=str, 
                        default=config.ALBUM_NAME, 
                        help="Name of iCloud Album to download.")
    
    parser.add_argument("-d", "--dir", type=str, 
                        default=config.DOWNLOAD_DIR, 
                        help="Local directory to download to.")
    
    parser.add_argument("-t", "--timeout", 
                        type=parse_timeout, # Use our custom fcn to process timeout value.
                        default=config.SOCKET_TIMEOUT,
                        help="Network socket time-out in seconds. Pass 'None' or 0 for infinite waiting.")
    
    # Use flags for booleans (True/False).
    # If pass --debug, the value will be True. Else (if not) - take from config.DEBUG_MODE
    parser.add_argument("--debug", action="store_true", 
                        default=config.DEBUG_MODE, 
                        help="Enable debug mode.")
    
    parser.add_argument("-o", "--auth-only", action="store_true",
                        default=False,
                        help="Only authenticate on Apple iCloud service. Do not download anything.")

    return parser.parse_args()
# ---------------------------------------------------------------------

def main():
    # args are already merged with config.py
    args = get_args()
    
    # Set up socket time-out (in seconds). 
    # If any network request hangs for more than that period, Python will throw a TimeoutError.
    socket.setdefaulttimeout(args.timeout)


    # Set up logging: if the flag is set, use DEBUG level, else use INFO level.
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format="  [DBG] %(message)s")

    # -------- EXAMPLES -------------------------------------------------------------------
    # В коде используем стандартный logging.debug
    #logging.debug("Запрашиваем метаданные у сервера...") # Напечатается только при --debug
    #logging.info("Скачивание завершено.")
    # ----------------------------------------------
    
    logging.debug("authenticate on Apple iCloud")
    api = functions.authenticate(args.user)
    logging.debug("Request list of all albums")
    functions.list_all_albums(api)
    
    if args.auth_only:
        print(f"\n   ---> Logging in Only. Skipping download. <---\n")
        sys.exit(0)

    # --- 
    logging.debug("Проверяем наличие нужного альбома.")
    if args.album not in api.photos.albums:
        print(f"\n❌ Ошибка: Альбом '{args.album}' не найден!")
        print(
            f"Если вы создали альбом на iPhone только что, "
            f"подождите 2–3 минуты, пока Apple синхронизирует его с сервером."
        )
        sys.exit(1)
    
    # --- 
    logging.debug("Prepare local directory to download to.")
    os.makedirs(args.dir, exist_ok=True)
    
    print(f"\nАльбом '{args.album}' найден! Начинаем скачивание...")
    photos = api.photos.albums[args.album]

    # --- 
    logging.debug("Получаем общее количество элементов, если альбом это поддерживает")
    total_count = len(photos) if hasattr(photos, "__len__") else "N/A"

    print(
        f"Альбом '{args.album}' выбран. Найдено элементов: {total_count}. Начинаем загрузку...\n"
    )

    # --- 
    logging.debug("Задаем счетчики")
    downloaded_count = 0
    skipped_count = 0
    errors_count = 0

    # --- 
    logging.debug("Запускаем цикл скачивания с автовозобновлением при ошибке 410 (одна попытка)")
    for idx, photo in enumerate(photos, start=1):
        logging.debug(" * Requesting the NEXT photo object from the server ...")
        
        #logging.debug("Generate file name and local path.")
        filepath, rel_path = functions.gen_local_path(photo, args.dir)
        
        if os.path.exists(filepath):
            print(
                f"Объект {idx} из {total_count}. Уже скачано, пропускаем: {rel_path}"
            )
            skipped_count += 1
            continue

        print(
            f"Объект {idx} из {total_count}. Скачивание: {rel_path} ({photo.size} байт)..."
        )

        try:
            logging.debug("Trying to download the given photo.")
            functions.get_photo(photo, filepath)
            downloaded_count += 1
        
        except Exception as e:
            if "410" in str(e):
                print(
                    f"  ⚠️  Ссылка устарела для объекта № {idx} ({rel_path}). Запрашиваем новый URL..."
                )
                try:
                    logging.debug(" ... Запрашиваем обновленный объект напрямую из библиотеки по его ID")
                    refreshed_photo = api.photos.all[photo.id]
                    filepath, rel_path = functions.gen_local_path(refreshed_photo, args.dir)
                    functions.get_photo(refreshed_photo, filepath)
                    
                    print(
                        f"   ✅ Успешно докачан объект № {idx} после обновления URL: {rel_path}"
                    )
                    downloaded_count += 1
                    
                except Exception as retry_e:
                    print(
                        f"  ❌ Объект № {idx}. Повторный сбой для {rel_path}: "
                        f"\n    оригинал действительно недоступен на сервере "
                        f"\n    ({retry_e})"
                    )
                    errors_count += 1
            else:
                print(
                    f"  ❌ Объект № {idx}. Ошибка при скачивании {rel_path}: "
                    f"\n    {e}"
                )
                errors_count += 1

    print(
        f"\n✅ Загрузка завершена! "
        f"\n  Всего объектов: {total_count}. Из них: "
        f"\n  * скачано файлов: {downloaded_count}, "
        f"\n  * уже были на месте: {skipped_count}, "
        f"\n  * не удалось скачать вследствие ошибок: {errors_count}."
    )
    
# ---------------------------------------------------------------------
if __name__ == "__main__":
    main()
