from mistralai import Mistral
import os

# Инициализация клиента
client = Mistral(api_key="ваш_api_ключ")

# Отправка запроса
response = client.chat.complete(
    model="mistral-small-latest",
    messages=[
        {"role": "user", "content": "Привет! Расскажи о себе."}
    ]
)

# Получение ответа
print(response.choices[0].message.content)