import os
import threading
import defusedxml.ElementTree as ET
from flask import Flask
import requests
import telebot
from telebot import types

TOKEN = "8887050197:AAF4SC3qXjsZaa7ARGLwKqM-S2ueF2cMjaM"
bot = telebot.TeleBot(TOKEN)

# Основные OPDS-каталоги из твоего списка для поиска книг
OPDS_FEEDS = [
    "http://flibusta.is/opds/search?searchTerm=",
    "http://coollib.net/opds/search?searchTerm=",
    "http://maxima-library.org/opds/search?searchTerm=",
]


@bot.message_handler(commands=["start"])
def send_welcome(message):
  bot.reply_to(
      message,
      "Привет! Я твой книжный бот «Книжная полка» 📚\nНапиши автора (например,"
      " *Стивен Кинг* или *Эрих Мария Ремарк*) или название книги, и я найду"
      " произведения на разных языках с возможностью сразу скачать .epub"
      " файл.",
      parse_mode="Markdown",
  )


@bot.message_handler(func=lambda message: True)
def search_books(message):
  query = message.text.strip()
  bot.send_message(
      message.chat.id,
      f"🔎 Ищу книги по запросу «{query}» во всех библиотеках и каталогах...",
  )

  found_books = []

  # Ищем по каталогам
  for base_url in OPDS_FEEDS:
    try:
      # Формируем поисковый запрос (кодируем пробелы)
      search_url = base_url + requests.utils.quote(query)
      headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
      response = requests.get(search_url, headers=headers, timeout=5)

      if response.status_code == 200:
        # Парсим XML/Atom ответ от OPDS каталога
        root = ET.fromstring(response.content)
        # Пространства имен для Atom фидов
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "opds": "http://opds-spec.org/2010/acquisition",
        }

        # Ищем записи о книгах
        for entry in root.findall("atom:entry", ns):
          title = entry.find("atom:title", ns)
          title_text = title.text if title is not None else "Без названия"

          # Ищем язык книги
          lang_elem = entry.find("atom:language", ns)
          lang = lang_elem.text if lang_elem is not None else "не указан"

          # Ищем ссылку на скачивание epub
          epub_link = None
          for link in entry.findall("atom:link", ns):
            rel = link.attrib.get("rel", "")
            type_attr = link.attrib.get("type", "")
            if "acquisition" in rel or "epub" in type_attr:
              epub_link = link.attrib.get("href")
              break

          if epub_link:
            # Если ссылка относительная, дополняем до абсолютной
            if epub_link.startswith("/"):
              base_domain = base_url.split("/opds")[0]
              epub_link = base_domain + epub_link

            found_books.append({
                "title": title_text,
                "lang": lang,
                "url": epub_link,
            })

            # Ограничим выдачу первыми 5 результатами, чтобы не перегружать чат
            if len(found_books) >= 5:
              break
    except Exception as e:
      continue

  if found_books:
    bot.send_message(
        message.chat.id,
        f"✅ Нашел несколько вариантов для «{query}». Выбирай и скачивай:",
    )

    for book in found_books:
      markup = types.InlineKeyboardMarkup()
      btn = types.InlineKeyboardButton(
          text="📥 Скачать .epub", url=book["url"]
      )
      markup.add(btn)

      bot.send_message(
          message.chat.id,
          f"📖 *{book['title']}*\n🌐 Язык: `{book['lang']}`",
          parse_mode="Markdown",
          reply_markup=markup,
      )
  else:
    bot.reply_to(
        message,
        f"К сожалению, по запросу «{query}» ничего не удалось вытянуть из"
        " каталогов. Попробуй уточнить запрос (например, написать имя на"
        " английском или точнее название).",
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
