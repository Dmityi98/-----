from Interface.IModel import IModel
from mistralai.client import Mistral
import os
import time
from dotenv import load_dotenv

load_dotenv()

class MistralModel(IModel):
    def __init__(self):
        self.model = os.getenv("NAME_MODEL", "mistral-large-latest")
        self.api_key = os.getenv("API_KEY")
        
        if not self.api_key:
            raise ValueError("API_KEY not found in .env")
        
        # Инициализация клиента (совместимо с mistralai 1.x - 2.x)
        self.client = Mistral(api_key=self.api_key)

    def answer(self, text_input: str) -> str:
        print(text_input)
        # === Промпт, заточенный под поиск дублей адресов ===
        prompt = f"""
        Проанализируй предоставленный текст и найди все упоминания адресов.

        Текст для анализа:
        {text_input}

        Задача:
        1. Извлеки все уникальные адреса из текста.
        2. Подсчитай точное количество упоминаний каждого адреса.
        3. Если адрес встречается белее — это норма (статус: ✅ OK).
        4. Если адрес встречается 1 раз — это аномалия (статус: ⚠️ Внимание).

        Правила:
        - Приводи адреса к единому виду: игнорируй регистр, лишние пробелы, сокращения (ул./улица, д./дом, кв./кв. и т.д.).
        - Считай дубликатами только те адреса, которые указывают на одно и то же место.
        - Не выдумывай адреса. Если в тексте адресов нет, сообщи об этом.

        Формат вывода:
        #### Отчёт по поиску дублей адресов

        | Адрес | Количество упоминаний | Статус |
        |-------|-----------------------|--------|
        | ...   | ...                   | ✅/⚠️  |

        **Итог:** [Краткое резюме: сколько адресов в норме, сколько требуют проверки]
        """

        try:
            time.sleep(1)  # Защита от rate-limit

            chat_response = self.client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Безопасное извлечение текста ответа
            if chat_response and getattr(chat_response, "choices", None) and len(chat_response.choices) > 0:
                report = chat_response.choices[0].message.content.strip()
            else:
                report = "⚠️ Нет ответа от модели"
            
            # Подсчёт токенов (с fallback для разных версий API)
            in_tokens = 0
            out_tokens = 0
            if chat_response and getattr(chat_response, "usage", None):
                usage = chat_response.usage
                in_tokens = getattr(usage, "input_tokens", 0) or getattr(usage, "prompt_tokens", 0) or 0
                out_tokens = getattr(usage, "output_tokens", 0) or getattr(usage, "completion_tokens", 0) or 0

            print(f"🪙 Токены: in={in_tokens}, out={out_tokens}, total={in_tokens + out_tokens}")
            return report

        except Exception as e:
            print(f"❌ Ошибка API: {str(e)}")
            return f"⚠️ Ошибка обработки: {str(e)}"