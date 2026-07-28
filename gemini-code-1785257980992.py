import os
import threading
from flask import Flask
import telebot
from telebot import types

TOKEN = "8887050197:AAF4SC3qXjsZaa7ARGLwKqM-S2ueF2cMjaM"
bot = telebot.TeleBot(TOKEN)

# База данных с примерами книг на разных языках и обложками
BOOKS_DATABASE = [
    {
        "title": "Три товарища (Drei Kameraden)",
        "author": "Эрих Мария Ремарк",
        "lang": "🇩🇪 Немецкий (Deutsch)",
        "cover": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c",
        "download_url": "https://example.com/remarque_de.epub",
    },
    {
        "title": "Три товарища",
        "author": "Эрих Мария Ремарк",
        "lang": "🇷🇺 Русский",
        "cover": "https://images.unsplash.com/photo-1512820790803-83ca734da794",
        "download_url": "https://example.com/remarque_ru.epub",
    },
    {
        "title": "Trīs draugi",
        "author": "Ērihs Marija Remarks",
        "lang": "🇱🇻 Латышский (Latviešu)",
        "cover": "https://images.unsplash.com/photo-1532012197267-da84d127e765",
        "download_url": "https://example.com/remarque_lv.epub",
    },
    {
        "title": "Three Comrades",
        "author": "Erich Maria Remarque",
        "lang": "🇬🇧 Английский (English)",
        "cover": "https://images.unsplash.com/photo-1495640388908-05fa85288e61",
        "download_url": "https://example.com/remarque_en.epub",
    },
]


@bot.message_handler(commands=["start"])
def send_welcome(message):
  bot.reply_to(
      message,
      "Привет! Я многоязычный книжный бот «Книжная полка» 📚\nНапиши название"
      " книги или автора, и я найду варианты на разных языках (русский, немецкий,"
      " латышский, английский) с обложками!",
  )


@bot.message_handler(func=lambda message: True)
def search_books(message):
  query = message.text.strip().lower()

  # Ищем совпадения в базе
  results = [
      b
      for b in BOOKS_DATABASE
      if query in b["title"].lower() or query in b["author"].lower()
  ]

  if results:
    for book in results:
      # Формируем красивое описание карточки книги
      caption = (
          f"📖 *{book['title']}*\n✍️ Автор: {book['author']}\n🌐 Язык:"
          f" {book['lang']}"
      )

      # Кнопка для скачивания ePub
      markup = types.InlineKeyboardMarkup()
      btn = types.InlineKeyboardButton(
          text="📥 Скачать ePub", url=book["download_url"]
      )
      markup.add(btn)

      # Отправляем фото-обложку вместе с информацией и кнопкой
      bot.send_photo(
          message.chat.id,
          photo=book["cover"],
          caption=caption,
          parse_mode="Markdown",
          reply_markup=markup,
      )
  else:
    bot.reply_to(
        message,
        "К сожалению, по твоему запросу ничего не нашлось. Попробуй написать"
        " «Ремарк» или «Три товарища».",
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
