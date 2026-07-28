import os
import threading
from urllib.parse import quote
from flask import Flask
import requests
import telebot
from telebot import types

TOKEN = "8887050197:AAF4SC3qXjsZaa7ARGLwKqM-S2ueF2cMjaM"
bot = telebot.TeleBot(TOKEN)

# Временное хранилище результатов поиска для кнопок
search_cache = {}


@bot.message_handler(commands=["start"])
def send_welcome(message):
  bot.reply_to(
      message,
      "Привет! Я книжный бот 📚\nНапиши название книги или автора, и я выведу"
      " список с интерактивными кнопками!",
      parse_mode="Markdown",
  )


@bot.message_handler(func=lambda message: True)
def search_books(message):
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

      response_text = f"📚 *Результаты по запросу: {query}*\n\n"
      markup = types.InlineKeyboardMarkup(row_width=4)
      buttons = []

      # Сохраняем в кэш для этого чата
      chat_id = message.chat.id
      search_cache[chat_id] = []

      for index, doc in enumerate(docs[:8], start=1):
        title = doc.get("title", "Без названия")
        authors_list = doc.get("author_name", ["Неизвестен"])
        author = authors_list[0] if authors_list else "Неизвестен"

        if len(title) > 40:
          title = title[:37] + "..."

        response_text += f"*{index}* {title} — *{author}*\n\n"

        ia_list = doc.get("ia", [])
        search_cache[chat_id].append(
            {"title": title, "author": author, "ia": ia_list}
        )

        # Создаем callback-кнопку (чтобы бот отлавливал нажатие внутри чата)
        buttons.append(
            types.InlineKeyboardButton(
                text=str(index), callback_data=f"book_{index-1}"
            )
        )

      markup.add(*buttons)
      # Добавляем нижнюю панель навигации в стиле примера
      markup.row(
          types.InlineKeyboardButton(text="1 / 1", callback_data="page_info"),
          types.InlineKeyboardButton(text=">", callback_data="next_page"),
      )

      bot.send_message(
          chat_id,
          response_text.strip(),
          parse_mode="Markdown",
          reply_markup=markup,
      )
    else:
      bot.reply_to(message, "Сервер библиотеки временно занят.")
  except Exception:
    bot.reply_to(message, "Произошла ошибка при поиске.")


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
  chat_id = call.message.chat.id
  data = call.data

  if data.startswith("book_"):
    index = int(data.split("_")[1])
    books = search_cache.get(chat_id, [])

    if index < len(books):
      book = books[index]
      title = book["title"]
      author = book["author"]
      ia_list = book["ia"]

      bot.answer_callback_query(call.id, text=f"Выбрано: {title}")

      if ia_list:
        identifier = ia_list[0]
        download_url = (
            f"https://archive.org/download/{identifier}/{identifier}.epub"
        )
        bot.send_message(
            chat_id,
            f"📖 *{title}*\n✍️ Автор: `{author}`\n📥 Ссылка на скачивание:"
            f" [Нажми сюда]({download_url})",
            parse_mode="Markdown",
        )
      else:
        bot.send_message(
            chat_id,
            f"📖 *{title}*\n✍️ Автор: `{author}`\n*(Прямой файл для этой книги в"
            " архиве отсутствует)*",
            parse_mode="Markdown",
        )
    else:
      bot.answer_callback_query(call.id, text="Информация устарела.")
  elif data == "next_page" or data == "page_info":
    bot.answer_callback_query(call.id, text="Показана первая страница выдачи.")


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
