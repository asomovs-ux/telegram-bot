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
      "Привет! Я твой книжный бот 📚\nНапиши название книги или автора,"
      " и я найду и пришлю готовый файл прямо в чат!",
      parse_mode="Markdown",
  )


@bot.message_handler(func=lambda message: True)
def search_and_send_book(message):
  query = message.text.strip()
  bot.send_message(
      message.chat.id,
      f"🔎 Ищу файлы для скачивания по запросу «{query}»...",
  )

  try:
    # Ищем через стабильный архивный каталог с прямыми файлами
    api_url = f"https://gutendex.com/books?search={requests.utils.quote(query)}"
    response = requests.get(api_url, timeout=12)

    if response.status_code == 200:
      results = response.json().get("results", [])
      sent_count = 0

      for book in results:
        title = book.get("title", "Без названия")
        authors_list = book.get("authors", [])
        author = (
            authors_list[0].get("name", "Неизвестен")
            if authors_list
            else "Неизвестен"
        )
        languages = ", ".join(book.get("languages", ["en"])).upper()

        formats = book.get("formats", {})
        target_url = None
        file_ext = ".epub"

        # Ищем именно файлы для скачивания
        for mime, url in formats.items():
          if "epub" in mime:
            target_url = url
            file_ext = ".epub"
            break
          elif "pdf" in mime:
            target_url = url
            file_ext = ".pdf"
            break
          elif "mobipocket-ebook" in mime:
            target_url = url
            file_ext = ".mobi"
            break

        if target_url:
          file_res = requests.get(target_url, timeout=15)
          if file_res.status_code == 200:
            safe_title = (
                title.replace("/", "_")
                .replace("\\", "_")
                .replace(":", "_")[:40]
            )
            file_name = f"{safe_title}{file_ext}"

            with open(file_name, "wb") as f:
              f.write(file_res.content)

            with open(file_name, "rb") as doc:
              bot.send_document(
                  message.chat.id,
                  doc,
                  caption=(
                      f"📖 *{title}*\n✍️ Автор: `{author}`\n🌐 Язык:"
                      f" `{languages}`\n📁 Формат: `{file_ext.upper()[1:]}`"
                  ),
                  parse_mode="Markdown",
              )

            os.remove(file_name)
            sent_count += 1

            # Отправляем до 3 файлов, чтобы не засорять чат
            if sent_count >= 3:
              break

      if sent_count == 0:
        bot.reply_to(
            message,
            "К сожалению, по этому запросу прямых файлов для скачивания не"
            " нашлось. Попробуй ввести название на английском языке (например,"
            " *Alice* или *Frankenstein*).",
        )
    else:
      bot.reply_to(message, "Ошибка при обращении к базе. Попробуй еще раз.")
  except Exception as e:
    bot.reply_to(message, "Произошла ошибка при поиске файла.")


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
