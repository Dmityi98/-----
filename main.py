import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import shutil
import os
from pathlib import Path
import threading 

# Попытка импорта контроллера. 
# Если путь неверен или есть ошибка импорта, приложение запустится, но покажет ошибку.
try:
    from Controller.Controller import Controller
    CONTROLLER_AVAILABLE = True
except ImportError as e:
    print(f"Критическая ошибка импорта: {e}")
    CONTROLLER_AVAILABLE = False

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.target_directory = "Download_Files/"
        self.controller = None
        if CONTROLLER_AVAILABLE:
            self.controller = Controller()
        
        self.files = []  
        self.downloads_path = Path.home() / "Downloads"
        self.file_labels = []  
        self.selected_label = None  
        self.is_generating = False  
        
        self.title("Отчет")
        self.geometry("500x500")
        self.resizable(False, False)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        # Кнопка выбора файлов
        self.open_button = ctk.CTkButton(self, text="Выбрать файлы", command=self.open_files)
        self.open_button.grid(row=0, column=1, sticky="n", padx=10, pady=10)

        # Список файлов
        self.fileListBox = ctk.CTkScrollableFrame(self, width=300, height=400)
        self.fileListBox.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)

        # Кнопка удаления
        self.delete_button = ctk.CTkButton(self, text="Удалить файл", command=self.delete_file)
        self.delete_button.grid(row=0, column=1, sticky="n", padx=10, pady=70)

        # Кнопка отчета
        self.report_button = ctk.CTkButton(self, text="Получить отчет", command=self.report)
        self.report_button.grid(row=0, column=1, sticky="n", padx=10, pady=130)
        
        # Лейбл статуса
        self.status_label = ctk.CTkLabel(self, text="Ожидание...", text_color="gray")
        self.status_label.grid(row=0, column=1, sticky="n", padx=10, pady=170)

        # Конфигурация сетки
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

    def open_files(self):
        filepaths = filedialog.askopenfilenames(
            initialdir=os.getcwd(),
            title="Выберите файлы",
            filetypes=(("Все файлы", "*.*"), ("Word файлы", "*.docx"), ("Text файлы", "*.txt"))
        )
        if filepaths:
            for filepath in filepaths:
                # Проверка на дубликаты
                if filepath in self.files:
                    continue
                    
                filename = os.path.basename(filepath)
                label = ctk.CTkLabel(self.fileListBox, text=filename, anchor="w", cursor="hand")
                label.pack(fill="x", padx=5, pady=2)
                label.bind("<Button-1>", lambda event, l=label: self.select_label(l))
                self.file_labels.append(label)
                self.files.append(filepath)

    def select_label(self, label):
        if self.selected_label:
            try:
                self.selected_label.configure(fg_color="transparent")
            except:
                pass # Виджет мог быть удален
       
        label.configure(fg_color="#032D50")  
        self.selected_label = label

    def delete_file(self):
        if self.selected_label:
            try:
                index = self.file_labels.index(self.selected_label)
                self.file_labels[index].destroy()
                self.file_labels.pop(index)
                self.files.pop(index)
                self.selected_label = None
            except ValueError:
                pass # Элемент уже удален

    def report(self):
        if not CONTROLLER_AVAILABLE:
            self.update_status("Ошибка: Контроллер не загружен (см. консоль)")
            return

        if self.is_generating or not self.files:
            if not self.files:
                self.update_status("Выберите файлы для обработки")
            return  
        
        os.makedirs(self.target_directory, exist_ok=True)

        self.is_generating = True
        self.report_button.configure(state="disabled", text="Генерация...")  
        self.update_status("Копирование файлов...")
 
        thread = threading.Thread(target=self.generate_report_in_thread)
        thread.daemon = True  
        thread.start()

    def generate_report_in_thread(self):
        try:
            # Очистка папки перед новым запуском (опционально)
            # for f in os.listdir(self.target_directory):
            #     os.remove(os.path.join(self.target_directory, f))

            for path in self.files:
                filename = os.path.basename(path)
                dest_path = os.path.join(self.target_directory, filename)
                shutil.copy(path, dest_path)
                print(f"Файл скопирован: {dest_path}")
            
            self.after(0, self.on_copy_complete)  
        except Exception as e:
            print(f"Ошибка при копировании: {e}")
            error_msg = f"Ошибка копирования: {e}"
            # FIX: Передаем ошибку через аргумент по умолчанию
            self.after(0, lambda msg=error_msg: self.on_error(msg))

    def on_copy_complete(self):
        self.update_status("Генерация отчёта (ИИ)...")
        try:
            if self.controller:
                self.controller.work()
            self.after(0, self.on_report_complete)
        except Exception as e:
            error_msg = f"Ошибка в controller.work(): {e}"
            # FIX: Передаем ошибку через аргумент по умолчанию
            self.after(0, lambda msg=error_msg: self.on_error(msg))

    def on_report_complete(self):
        # Очищаем список файлов в интерфейсе
        for label in self.file_labels:
            try:
                label.destroy()
            except:
                pass
        self.file_labels.clear()
        self.files.clear()
        
        self.update_status("Отчёт готов! Сохранен в Загрузки")

        # Копирование отчета в Загрузки
        report_file = "Отчет.txt"
        if os.path.exists(report_file):
            destination = self.downloads_path / "Отчёт.txt"
            try:
                shutil.copy(report_file, destination)
                print(f"Отчет скопирован в: {destination}")
            except Exception as e:
                print(f"Не удалось скопировать отчет в загрузки: {e}")
        else:
            print("Файл Отчет.txt не найден после работы контроллера")

        self.is_generating = False
        self.report_button.configure(state="normal", text="Получить отчет")

    def on_error(self, message):
        self.update_status(f"Ошибка: {message}")
        self.is_generating = False
        self.report_button.configure(state="normal", text="Получить отчет")

    def update_status(self, text):
        try:
            self.status_label.configure(text=text)
        except:
            pass # Окно могло быть закрыто

if __name__ == "__main__":
    app = App()
    app.mainloop()