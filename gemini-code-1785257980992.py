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
      "Привет! Я книжный бот 📚\nНапиши название книги или автора, и я найду"
      " для тебя варианты с обложками и кнопками скачивания в разных"
      " форматах!",
      parse_mode="Markdown",
  )


@bot.message_handler(func=lambda message: True)
def search_books(message):
  query = message.text.strip()
  bot.send_message(
      message.chat.id, f"🔎 Ищу книги и доступные форматы по запросу «{query}»..."
  )

  try:
    api_url = f"https://gutendex.com/books?search={requests.utils.quote(query)}"
    response = requests.get(api_url, timeout=12)

    if response.status_code == 200:
      data = response.json()
      results = data.get("results", [])

      if not results:
        bot.reply_to(
            message,
            "К сожалению, по этому запросу ничего не нашлось. Попробуй другое"
            " название.",
        )
        return

      sent_count = 0
      for book in results[:3]:  # Показываем до 3 вариантов
        title = book.get("title", "Без названия")
        authors_list = book.get("authors", [])
        author = (
            authors_list[0].get("name", "Неизвестен")
            if authors_list
            else "Неизвестен"
        )
        languages = ", ".join(book.get("languages", ["en"])).upper()

        # Ищем обложку книги (обычно image/jpeg)
        formats = book.get("formats", {})
        cover_url = None
        for mime, url in formats.items():
          if "image/jpeg" in mime:
            cover_url = url
            break

        # Создаем клавиатуру с несколькими форматами для скачивания
        markup = types.InlineKeyboardMarkup()
        has_formats = False

        for mime, url in formats.items():
          if "epub" in mime:
            markup.add(
                types.InlineKeyboardButton(
                    text="📥 Скачать .EPUB", url=url
                )
            )
            has_formats = True
          elif "pdf" in mime:
            markup.add(
                types.InlineKeyboardButton(text="📥 Скачать .PDF", url=url)
            )
            has_formats = True
          elif "plain" in mime and "utf-8" in mime:
            markup.add(
                types.InlineKeyboardButton(text="📥 Скачать .TXT", url=url)
            )
            has_formats = True

        if not has_formats:
          continue

        caption = (
            f"📖 *{title}*\n✍️ Автор: `{author}`\n🌐 Язык: `{languages}`"
        )

        # Отправляем сообщение с обложкой (если она есть) или текстовую карточку
        if cover_url:
          try:
            bot.send_photo(
                message.chat.id,
                cover_url,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=markup,
            )
          except Exception:
            bot.send_message(
                message.chat.id,
                caption,
                parse_mode="Markdown",
                reply_markup=markup,
            )
        else:
          bot.send_message(
              message.chat.id,
              caption,
              parse_mode="Markdown",
              reply_markup=markup,
          )

        sent_count += 1
        if sent_count >= 3:
          break

      if sent_count == 0:
        bot.reply_to(
            message,
            "Книги найдены, но у них нет открытых файлов для скачивания.",
        )
    else:
      bot.reply_to(message, "Ошибка при обращении к базе данных.")
  except Exception:
    bot.reply_to(message, "Произошла ошибка при поиске. Попробуй еще раз.")


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
