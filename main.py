import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from Controller.Controller import Controller
import shutil
import os
from pathlib import Path
import threading  

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.target_directory = "Download_Files/"
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

        self.open_button = ctk.CTkButton(self, text="Выбрать файлы", command=self.open_files)
        self.open_button.grid(row=0, column=1, sticky="n", padx=10, pady=10)

        self.fileListBox = ctk.CTkScrollableFrame(self)
        self.fileListBox.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)

        self.delete_button = ctk.CTkButton(self, text="Удалить файл", command=self.delete_file)
        self.delete_button.grid(row=0, column=1, sticky="n", padx=10, pady=70)

        self.columnconfigure(0, weight=1)
        self.columnconfigure([0, 1, 2, 3], weight=1)

        self.report_button = ctk.CTkButton(self, text="Получить отчет", command=self.report)
        self.report_button.grid(row=0, column=1, sticky="n", padx=10, pady=130)
        self.report_button.focus_set()  # Устанавливаем фокус на кнопку
        self.focus_force()

        # Добавлено: лейбл для статуса
        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.grid(row=0, column=1, sticky="n", padx=10, pady=170)

    def open_files(self):
        filepaths = filedialog.askopenfilenames(
            initialdir=os.getcwd(),
            title="Выберите файлы",
            filetypes=(("Все файлы", "*.*"),)
        )
        if filepaths:
            for filepath in filepaths:
                filename = os.path.basename(filepath)
                label = ctk.CTkLabel(self.fileListBox, text=filename)
                label.pack(fill="x", padx=5, pady=5)
                label.bind("<Button-1>", lambda event, l=label: self.select_label(l))
                self.file_labels.append(label)
                self.files.append(filepath)

    def select_label(self, label):
        if self.selected_label:
            self.selected_label.configure(fg_color="transparent")
       
        label.configure(fg_color="#032D50")  
        self.selected_label = label

    def delete_file(self):
        if self.selected_label:
            index = self.file_labels.index(self.selected_label)
            self.file_labels[index].destroy()
            self.file_labels.pop(index)

            self.files.pop(index)
            self.selected_label = None

    def report(self):
        if self.is_generating or not self.files:
            return  
        
        os.makedirs("Download_Files", exist_ok=True)

        self.is_generating = True
        self.report_button.configure(state="disabled", text="Генерация...")  
        self.update_status("Копирование файлов...")
 
        thread = threading.Thread(target=self.generate_report_in_thread)
        thread.daemon = True  
        thread.start()

    def generate_report_in_thread(self):
        try:
            for path in self.files:
                filename = os.path.basename(path)
                dest_path = os.path.join(self.target_directory, filename)
                print(dest_path)
                shutil.copy(path, dest_path)
                print(f"Файл успешно скопирован в: {dest_path}")
            
            self.after(0, self.on_copy_complete)  
        except Exception as e:
            print(f"Ошибка при копировании: {e}")
            self.after(0, lambda: self.on_error(f"Ошибка копирования: {e}"))

    def on_copy_complete(self):
        self.update_status("Генерация отчёта...")
        try:
            self.controller.work()
            self.after(0, self.on_report_complete)
        except Exception as e:
            self.after(0, lambda: self.on_error(f"Ошибка в controller.work(): {e}"))

    def on_report_complete(self):

        for label in self.file_labels:
            label.destroy()
        self.files.clear()
        self.update_status("Отчёт готов! и сохранен в загрузки")

        report_file = "Отчет.txt"  # ← путь к твоему сформированному отчёту
        destination = self.downloads_path / "Отчёт.txt"

        shutil.copy(report_file, destination)
        self.is_generating = False
        self.report_button.configure(state="normal", text="Получить отчет")

    def on_error(self, message):
        self.update_status(f"Ошибка: {message}")
        self.is_generating = False
        self.report_button.configure(state="normal", text="Получить отчет")

    def update_status(self, text):
        self.status_label.configure(text=text)
        self.update()  

if __name__ == "__main__":
    app = App()
    app.mainloop()