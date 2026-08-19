1. Готовим окружение Conda:
```bash
conda create --name icloud_env python=3.11 -y
```

2. Заходим в него, устанавливаем библиотеку `pyicloud`:
```bash
user@local-host:~$ conda activate icloud_env 
(icloud_env) user@local-host:~$ pip install pyicloud
```

3. Находясь в означенном окружении Conda, запрашиваем путь к интерпретатору Python этого окружения:
```bash
(icloud_env) user@local-host:~$ which python
```
Получаем ответ наподобие:
`/home/user/.local/bin/miniconda3/envs/icloud_env/bin/python`
Запоминаем его, он потребуется на последующем шаге.

Теперь окружение Conda можно деактивировать:
```bash
conda deactivate
```
Оно может понадобиться разве что для отладки и экспериментов.

4. Создаем файл `config.py` из шаблона `config.example.py`.
Редактируем его, вносим необходимые изменения.

__N.B.__ Почти все параметры, кроме `TARGET_PYTHON` можно изменять аргументами командной строки
при вызове `dldr.py` и `organize_existing.py`.
Также нельзя отключить `DEBUG_MODE = True` из командной строки; можно только включить его назад,
если в конфиге написано `DEBUG_MODE = False`.

5. В созданном файле `config.py` изменяем значение переменной `TARGET_PYTHON` так, 
чтобы оно указывало на ответ, полученный на шаге (3):
```
TARGET_PYTHON = "/home/user/.local/bin/miniconda3/envs/icloud_env/bin/python"
```

6. Изучаем аргументы командной строки:
```bash
./dldr.py --help
./organize_existing.py --help
```

7. Наслаждаемся скачанными фото и видео.
