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
      "Привет! Я книжный бот «Книжная полка» 📚\nНапиши автора или название"
      " книги (например, *Remarque*, *King* или *Alice*), и я найду для тебя"
      " файлы в формате .epub.",
      parse_mode="Markdown",
  )


@bot.message_handler(func=lambda message: True)
def search_books(message):
  query = message.text.strip()
  bot.send_message(
      message.chat.id, f"🔎 Ищу книги по запросу «{query}» в открытых каталогах..."
  )

  found_books = []

  try:
    # Используем официальный открытый API Project Gutenberg для поиска книг
    api_url = f"https://gutendex.com/books?search={requests.utils.quote(query)}"
    response = requests.get(api_url, timeout=7)

    if response.status_code == 200:
      data = response.json()
      results = data.get("results", [])

      for book in results[:6]:  рассматриваем первые 6 результатов
        title = book.get("title", "Без названия")
        languages = ", ".join(book.get("languages", ["en"])).upper()

        # Ищем прямую ссылку на epub формат в форматах книги
        formats = book.get("formats", {})
        epub_url = None
        for mime, url in formats.items():
          if "epub" in mime:
            epub_url = url
            break

        if epub_url:
          authors_list = book.get("authors", [])
          author_name = (
              authors_list[0].get("name", "Неизвестен")
              if authors_list
              else "Неизвестен"
          )

          found_books.append({
              "title": title,
              "author": author_name,
              "lang": languages,
              "url": epub_url,
          })
  except Exception as e:
    pass

  if found_books:
    bot.send_message(
        message.chat.id,
        f"✅ Нашел книги по запросу «{query}». Выбирай и скачивай:",
    )

    for book in found_books:
      markup = types.InlineKeyboardMarkup()
      btn = types.InlineKeyboardButton(
          text="📥 Скачать .epub", url=book["url"]
      )
      markup.add(btn)

      bot.send_message(
          message.chat.id,
          f"📖 *{book['title']}*\n✍️ Автор: `{book['author']}`\n🌐 Язык:"
          f" `{book['lang']}`",
          parse_mode="Markdown",
          reply_markup=markup,
      )
  else:
    bot.reply_to(
        message,
        f"К сожалению, по запросу «{query}» ничего не найдено. Попробуй ввести"
        " название на английском или немецком языке (например, *Remarque* или"
        " *Frankenstein*).",
        parse_mode="Markdown",
    )


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
