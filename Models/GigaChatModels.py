from Interface.IModel import IModel
import os
import re
import time
from dotenv import load_dotenv
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

load_dotenv()

class GigaChatModel(IModel):
    def __init__(self):
        self.auth_token = "MWMzMjAwNTYtMzNhNi00ZmMwLTgzMzctYzc0NTUwNDBkNjU5Ojc2MmVjNDRjLWJjMTEtNDFjZS1hYmQ1LTYzYTYwZGRiNjQ1Yg=="
        if not self.auth_token:
            raise ValueError("GIGACHAT_AUTH_TOKEN not found in .env")

        self.client = GigaChat(credentials=self.auth_token, scope="GIGACHAT_API_PERS", verify_ssl_certs=False,)

    def answer(self, registration_text: str, text_order: str) -> str:
        # Шаг 1: Извлечь уникальные номера МО
        mo_pattern = r'МО №(\d+/\d+)'
        mo_numbers = set(re.findall(mo_pattern, registration_text, re.IGNORECASE))
        print(f"MO Numbers: {mo_numbers}")
        if not mo_numbers:
            return "Изменений не выявлено (номера МО не найдены в регистрации)."

        # Шаг 2: Разбить text_order на чанки по МО
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

        # Шаг 3: Сравнение для каждого МО
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
            docx_lines = [line for line in registration_text.split('\n') if mo_num.lower() in line.lower()]
            docx_chunk = '\n'.join(docx_lines)
            excel_chunk = excel_chunks.get(mo_num, '')
            if not excel_chunk.strip():
                report_parts.append(f"МО №{mo_num} — Новый адрес (не найден в книге регистрации):\n{docx_chunk}")
                continue

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

            try:
                time.sleep(60)  # Задержка, чтобы не превысить лимиты API

                messages = [
                    Messages(role=MessagesRole.SYSTEM, content="Ты — ассистент, который помогает анализировать данные."),
                    Messages(role=MessagesRole.USER, content=prompt)
                ]

                chat_response = self.client.chat(Chat(messages=messages))

                mo_report = chat_response.choices[0].message.content
                print(f"Длина ответа: {len(mo_report)}")

                # Подсчёт токенов
                if hasattr(chat_response, 'usage') and chat_response.usage:
                    input_tokens = chat_response.usage.prompt_tokens
                    output_tokens = chat_response.usage.completion_tokens
                    total_input_tokens += input_tokens
                    total_output_tokens += output_tokens
                    print(f"Токены для МО №{mo_num}: Input={input_tokens}, Output={output_tokens}")

                report_parts.append(f"### МО №{mo_num}\n{mo_report}")
                print(f"Обработано МО №{mo_num}")
            except Exception as e:
                print(f"Ошибка API для МО №{mo_num}: {str(e)}")
                report_parts.append(f"### МО №{mo_num}\nОшибка обработки: {str(e)}")

        full_report = '\n\n---\n\n'.join(report_parts) if report_parts else "Изменений не выявлено"

        # Итоговый подсчёт токенов
        total_tokens = total_input_tokens + total_output_tokens
        print(f"\n=== ИТОГОВЫЙ ПОДСЧЁТ ТОКЕНОВ ===")
        print(f"Общее на запросы (input): {total_input_tokens}")
        print(f"Общее на ответы (output): {total_output_tokens}")
        print(f"Общее количество: {total_tokens}")

        token_summary = f"\n\n### Итоговый подсчёт токенов\n- Input: {total_input_tokens}\n- Output: {total_output_tokens}\n- Total: {total_tokens}"
        full_report += token_summary

        print(full_report)
        return full_report
