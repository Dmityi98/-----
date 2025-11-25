from Interface.IModel import IModel
from mistralai import Mistral
import os
import re
import time
from dotenv import load_dotenv

load_dotenv()

class MistralModel(IModel):
    def __init__(self):
        self.model = os.getenv("NAME_MODEL", "mistral-large-latest")
        self.api_key = os.getenv("API_KEY")
        print(self.api_key)
        if not self.api_key:
            raise ValueError("API_KEY not found in .env")
        self.client = Mistral(api_key=self.api_key)

    def answer(self, registration_text, text_order):
        mo_pattern = r'МО №(\d+/\d+)'
        mo_numbers = set(re.findall(mo_pattern, registration_text, re.IGNORECASE))
        print(f"MO Numbers: {mo_numbers}")  
        if not mo_numbers:
            return "Изменений не выявлено (номера МО не найдены в регистрации)."

        mo_pattern_excel = r'^(\d+/\d+)'
        excel_chunks = {}
        lines = text_order.strip().split('\n')
        current_mo = None
        current_chunk = []

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            mo_match = re.match(mo_pattern_excel, line_stripped, re.IGNORECASE)
            if mo_match:
                if current_mo:
                    excel_chunks[current_mo] = '\n'.join(current_chunk)
                current_mo = mo_match.group(1)
                current_chunk = [line_stripped]
            elif current_mo:
                current_chunk.append(line_stripped)
        if current_mo:
            excel_chunks[current_mo] = '\n'.join(current_chunk)
        print(f"Excel Chunks keys: {list(excel_chunks.keys())}")


        report_parts = []
        total_input_tokens = 0  
        total_output_tokens = 0  

        few_shot = """
        Пример сравнения адресов и графиков работы:
        Эталон (Книга):
        с. Кугушево, ул. Пришкольная, д. 1; понедельник (1-я и 5-я недели): 11:10 - 15:40 (перерыв: 12:30 - 13:00).

        Новое (Распоряжение):
        с. Кугушево, ул. Пришкольная, д. 1; понедельник (1-я и 5-я недели): 11:10 - 15:40 (перерыв: 12:30 - 13:00).

        Анализ:
        - Адрес: Без изменений.
        - График работы: Без изменений.
        """

        for mo_num in sorted(mo_numbers):
            # Чанк из Docx
            docx_lines = [line for line in registration_text.split('\n') if mo_num.lower() in line.lower()]
            docx_chunk = '\n'.join(docx_lines)

            # Чанк из Excel
            excel_chunk = excel_chunks.get(mo_num, '')

            if not excel_chunk.strip():
                report_parts.append(f"МО №{mo_num} — Новый адрес (не найден в книге регистрации):\n{docx_chunk}")
                continue

            # print(f"Чанк из распоряжения: {docx_chunk}")
            # print(f"Чанк из книги регистрации: {excel_chunk}")

            # Индивидуальный промпт для этого МО
            prompt = f"""
            {few_shot}

            Теперь проанализируй только для МО №{mo_num}.

            Книга регистрации (эталонные данные):
            {excel_chunk}

            Распоряжение (новые данные):
            {docx_chunk}

            Задача:
            1. Сравни адреса (населённый пункт, улица, дом).
            2. Сравни графики работы (дни недели, недели, время, перерывы).

            Правила:
            - Если адрес отличается, отмечай это как изменение.
            - Если график работы отличается (время, дни, недели, перерывы), отмечай это как изменение.
            - Если всё совпадает, указывай "Без изменений".

            Формат вывода:
            #### Сравнение для МО №{mo_num}

            | **Локация**       | **Эталонный адрес**       | **Новый адрес**         | **Изменения в адресе** |
            |-------------------|---------------------------|-------------------------|------------------------|
            | с. Кугушево       | ул. Пришкольная, д. 1     | ул. Пришкольная, д. 1   | Без изменений         |

            | **Локация**       | **Эталонный график**                     | **Новый график**                     | **Изменения в графике** |
            |-------------------|------------------------------------------|--------------------------------------|-------------------------|
            | с. Кугушево       | Пн (1-я и 5-я недели): 11:10–15:40 (перерыв 12:30–13:00) | Пн (1-я и 5-я недели): 11:10–15:40 (перерыв 12:30–13:00) | Без изменений |
            """

            print(f"Длина промпта: {len(prompt)}")

            try:
                time.sleep(100)
                chat_response = self.client.chat.complete(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}]
                )
                mo_report = chat_response.choices[0].message.content.strip()
                print(f"Длина ответа: {len(mo_report)}")

                if chat_response.usage:
                    input_tokens = chat_response.usage.prompt_tokens
                    output_tokens = chat_response.usage.completion_tokens
                    total_input_tokens += input_tokens
                    total_output_tokens += output_tokens
                    print(f"Токены для МО №{mo_num}: Input={input_tokens}, Output={output_tokens}")
                else:
                    print(f"Usage не доступен для МО №{mo_num}")
                
                report_parts.append(f"### МО №{mo_num}\n{mo_report}")
                print(f"Обработано МО №{mo_num}")
                time.sleep(1)
            except Exception as e:
                print(f"Ошибка API для МО №{mo_num}: {str(e)}")
                report_parts.append(f"### МО №{mo_num}\nОшибка обработки: {str(e)}")

        full_report = '\n\n---\n\n'.join(report_parts) if report_parts else "Изменений не выявлено"
        
        total_tokens = total_input_tokens + total_output_tokens

        print(f"\n=== ИТОГОВЫЙ ПОДСЧЁТ ТОКЕНОВ ===")
        print(f"Общее на запросы (input): {total_input_tokens}")
        print(f"Общее на ответы (output): {total_output_tokens}")
        print(f"Общее количество: {total_tokens}")
        
        print(full_report)
        return full_report