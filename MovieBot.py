import telebot
import os
from typing import Dict
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

load_dotenv()
TELEGRAM_TOKEN = "8330197118:AAHqB3kC1d9qTGhtNIitFf-K97SQPRMCDqg"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY

# Telegram bot

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# LLM

llm = ChatOpenAI(
    model="google/gemini-2.0-flash-exp:free",
    temperature=0.7,
    openai_api_base="https://openrouter.ai/api/v1"
)

# Prompt

MOVIE_PROMPT = PromptTemplate(
    input_variables=["city", "user_query"],
    template="""
Ты помощник по кино. Пользователь из города {city} спрашивает: "{user_query}".

Доступные крупные кинотеатры в российских городах:
Москва: "Каро", "Синема Парк", "Формула Кино"
СПб: "Аврора", "Пионер", "Кронверк"
Екатеринбург: "Киномакс", "Синергия"
Новосибирск: "Киномакс", "Мир"
Казань: "Татнефть-АЗС Киномакс"

Сейчас в кинотеатрах идут новинки:
- "Дюна 2"
- "Годзилла минус один"
- "Мальчик и цыпленок"
- "Пятница 13-е"
- "Матильда"

Ответь:
1. Какие новинки идут в кинотеатрах {city}
2. Где именно их показывают
3. Примерное время сеансов
4. Жанр и краткое описание
5. Ссылки на покупку билетов

Формат: кратко, по делу
"""
)

# LCEL цепочка

movie_chain = MOVIE_PROMPT | llm

# Хранение городов

user_cities: Dict[int, str] = {}

# Handlers

@bot.message_handler(commands=["start"])
def start_message(message):
    bot.send_message(
        message.chat.id,
        "Привет! Я помогу найти фильмы в кинотеатрах твоего города!\n"
        "Напиши /setcity имя города — чтобы указать город\n"
        "Или просто спроси про кино"
    )

@bot.message_handler(commands=["setcity"])
def set_city(message):
    try:
        city = message.text.split(" ", 1)[1]
        user_cities[message.from_user.id] = city
        bot.reply_to(message, f"Город установлен: {city}")
    except IndexError:
        bot.reply_to(message, "Напиши: /setcity имя города")

@bot.message_handler(commands=["help"])
def help_command(message):
    bot.reply_to(
        message,
        "🎬 Команды:\n"
        "/start — начать\n"
        "/setcity имя города — выбрать город\n"
        "/nowplaying — что идёт сейчас\n\n"
        "Или просто пиши: «какие новинки в кино»"
    )

@bot.message_handler(commands=["nowplaying"])
def now_playing(message):
    city = user_cities.get(message.from_user.id, "Москва")
    response = movie_chain.invoke(
        {"city": city, "user_query": "какие фильмы идут сейчас"}
    )
    bot.reply_to(message, response.content)

@bot.message_handler(content_types=["text"])
def handle_movie_query(message):
    city = user_cities.get(message.from_user.id, "Москва")
    try:
        response = movie_chain.invoke(
            {"city": city, "user_query": message.text}
        )
        bot.reply_to(message, response.content)
    except Exception as e:
        bot.reply_to(
            message,
            f"Ошибка: {str(e)[:120]}\nПопробуй /setcity имя города"
        )

# Run

if __name__ == "__main__":
    print("Кино-бот запущен!")
    bot.infinity_polling()
