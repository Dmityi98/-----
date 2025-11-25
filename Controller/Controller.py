from Models.MistralModels import MistralModel
#from Models.GigaChatModels import GigaChatModel
from Service.DocxService import DocxService
from Service.ExcelService import ExcelService
import os
import datetime
import shutil
class Controller:

    def __init__(self):
        self.model = MistralModel()
        self.__folderPath = "Download_Files"
        self.docx_service = DocxService()
        self.excel_service = ExcelService()


    
    def work(self):
        print(datetime.datetime.now())
        registration_text = ""
        text_order = ""
        print("Работа контролеера")
        files = os.listdir(self.__folderPath)

        for item in files:
            name,ext = os.path.splitext(item)
            if ext == ".docx":
                registration_text = self.docx_service.read_file(item)
            if ext == ".xlsx":
                text_order = self.excel_service.read_file(item)

        answer_from_model = self.model.answer(registration_text, text_order)
        print(datetime.datetime.now())
        file = open("Отчет.txt", "w", encoding="utf-8")
        file.write(answer_from_model)
        file.close()

        shutil.rmtree(self.__folderPath)
        os.makedirs(self.__folderPath) 