import os
import threading
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
      "Привет! Я книжный бот «Книжная полка» 📚\nНапиши название книги или"
      " автора (например, *King*, *Orwell* или *Remarque*), и я найду для тебя"
      " файлы.",
      parse_mode="Markdown",
  )


@bot.message_handler(func=lambda message: True)
def search_books(message):
  query = message.text.strip()
  bot.send_message(
      message.chat.id, f"🔎 Ищу книги по запросу «{query}» в открытой базе..."
  )

  try:
    # Используем стабильный поиск по библиотеке Open Library
    url = f"https://openlibrary.org/search.json?q={requests.utils.quote(query)}"
    response = requests.get(url, timeout=7)

    if response.status_code == 200:
      data = response.json()
      docs = data.get("docs", [])

      found = 0
      for doc in docs[:5]:
        title = doc.get("title", "Без названия")
        author = ", ".join(doc.get("author_name", ["Неизвестен"]))

        # Идемходим ID для ссылки на чтение/скачивание
        epub_link = f"https://openlibrary.org{doc.get('key', '')}"

        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton(
            text="📥 Открыть / Скачать", url=epub_link
        )
        markup.add(btn)

        bot.send_message(
            message.chat.id,
            f"📖 *{title}* \n✍️ Автор: `{author}`",
            parse_mode="Markdown",
            reply_markup=markup,
        )
        found += 1

      if found == 0:
        bot.reply_to(
            message, f"К сожалению, по запросу «{query}» ничего не нашлось."
        )
    else:
      bot.reply_to(message, "Ошибка при обращении к библиотеке. Попробуй позже.")
  except Exception as e:
    bot.reply_to(message, "Произошла ошибка при поиске.")


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
