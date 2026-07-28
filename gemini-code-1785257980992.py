import os
import threading
from urllib.parse import quote
from flask import Flask
import requests
import telebot
from telebot import types

TOKEN = "8887050197:AAF4SC3qXjsZaa7ARGLwKqM-S2ueF2cMjaM"
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start"])
def send_welcome(message):
  bot.reply_to(
      message,
      "Привет! Я книжный бот 📚\nНапиши название книги или автора (или"
      " используй команду, например `/братья Стругацкие`), и я выведу список с"
      " кнопками выбора!",
      parse_mode="Markdown",
  )


@bot.message_handler(func=lambda message: True)
def search_books(message):
  # Убираем слеш, если пользователь написал команду вроде /братья Стругацкие
  query = message.text.lstrip("/").strip()
  if not query:
    return

  bot.send_message(
      message.chat.id, f"🔎 Ищу книги по запросу «{query}», подожди..."
  )

  try:
    encoded_query = quote(query)
    api_url = f"https://openlibrary.org/search.json?q={encoded_query}"
    response = requests.get(api_url, timeout=12)

    if response.status_code == 200:
      data = response.json()
      docs = data.get("docs", [])

      if not docs:
        bot.reply_to(message, "К сожалению, по этому запросу ничего не нашлось.")
        return

      # Формируем красивый список как на вашем скриншоте
      response_text = ""
      markup = types.InlineKeyboardMarkup(row_width=4)
      buttons = []

      # Берем до 8 вариантов, чтобы поместились на экран и в кнопки
      for index, doc in enumerate(docs[:8], start=1):
        title = doc.get("title", "Без названия")
        authors_list = doc.get("author_name", ["Неизвестен"])
        author = authors_list[0] if authors_list else "Неизвестен"

        # Ограничиваем длину текста для красоты
        if len(title) > 45:
          title = title[:42] + "..."

        response_text += (
            f"*{index}* Компактно: *{title}* — `{author}`\n\n"
            if False
            else f"*{index}* {title} — *{author}*\n\n"
        )

        # Создаем кнопку для каждого номера
        key = doc.get("key", "")
        book_url = (
            f"https://openlibrary.org{key}" if key else "https://openlibrary.org"
        )
        buttons.append(
            types.InlineKeyboardButton(text=str(index), url=book_url)
        )

      # Добавляем кнопки рядами по 4 штуки
      markup.add(*buttons)

      # Отправляем единым сообщением со списком и кнопками
      bot.send_message(
          message.chat.id,
          response_text.strip(),
          parse_mode="Markdown",
          reply_markup=markup,
      )
    else:
      bot.reply_to(message, "Сервер библиотеки временно занят. Попробуй еще раз.")
  except Exception:
    bot.reply_to(message, "Произошла ошибка при поиске. Попробуй другой запрос.")


# --- Веб-сервер Flask (для Render) ---
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot is alive!"


def run_web():
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)


web_thread = threading.Thread(target=run_web)
web_thread.start()

if __name__ == "__main__":
  bot.infinity_polling()
