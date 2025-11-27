Автоматизация Отчетности по МО

📝 Описание
Автоматизация Отчетности по МО — это Python-приложение для автоматизированного процесса сравнения по (МО). 


Python: 3.10 или выше.
Виртуальное окружение: Рекомендуется (venv или conda).
Библиотеки: Устанавливаются из requirements.txt (включая python-docx, customtkinter для GUI).

🚀 Установка и Запуск
Шаг 1: Клонирование и Подготовка
Bashgit clone <your-repo-url>  # Или скачайте архив
cd Отчет  # Название папки проекта
Шаг 2: Создание Виртуального Окружения
Bash# Создайте venv
python -m venv Reportvenv

# Активируйте (macOS/Linux)
source Reportvenv/bin/activate

# Активируйте (Windows)
Reportvenv\Scripts\activate


Шаг 3: Установка Библиотек
Bashpip install -r requirements.txt
Примечание: Если возникнут конфликты (например, с lxml и python-docx), обновите: pip install --upgrade python-docx lxml.


Шаг 4: Настройка .env
Создайте файл .env в корне проекта и добавьте:
env# API настройки (замените на ваши значения)
MODEL_NAME=your-model-name  # 
API_KEY=your-api-key-here  # 



Шаг 5: Запуск
Bashpython main.py
