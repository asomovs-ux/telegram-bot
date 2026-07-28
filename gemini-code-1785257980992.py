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
      "Привет! Я твой книжный бот 📚\nНапиши название книги или автора"
      " (например, *Stephen King*, *Remarque* или *Orwell*), и я тщательно"
      " проверю все доступные каталоги, чтобы прислать файл прямо в чат!",
      parse_mode="Markdown",
  )


@bot.message_handler(func=lambda message: True)
def search_and_send_book(message):
  query = message.text.strip()
  bot.send_message(
      message.chat.id,
      f"🔎 Тщательно ищу материалы по запросу «{query}» по всем базам...",
  )

  found_books = []

  # 1. Тщательная проверка через первый каталог (Gutendex / Project Gutenberg)
  try:
    api_url = f"https://gutendex.com/books?search={requests.utils.quote(query)}"
    response = requests.get(api_url, timeout=10)
    if response.status_code == 200:
      results = response.json().get("results", [])
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
          found_books.append({
              "title": title,
              "author": author,
              "lang": languages,
              "url": target_url,
              "ext": file_ext,
          })
  except Exception as e:
    pass

  # 2. Если в первом каталоге пусто, проверяем второй каталог (Open Library)
  if not found_books:
    try:
      ol_url = f"https://openlibrary.org/search.json?q={requests.utils.quote(query)}"
      ol_resp = requests.get(ol_url, timeout=10)
      if ol_resp.status_code == 200:
        docs = ol_resp.json().get("docs", [])
        for doc in docs[:3]:
          title = doc.get("title", "Без названия")
          author = ", ".join(doc.get("author_name", ["Неизвестен"]))
          key = doc.get("key", "")
          if key:
            found_books.append({
                "title": title,
                "author": author,
                "lang": "EN",
                "url": f"https://openlibrary.org{key}",
                "ext": ".html",
            })
    except Exception as e:
      pass

  # Отправляем результаты пользователю
  if found_books:
    sent_count = 0
    for book in found_books[:3]:  # Берем до 3 лучших вариантов
      try:
        if book["ext"] != ".html":
          # Скачиваем и шлем файл напрямую
          file_res = requests.get(book["url"], timeout=15)
          if file_res.status_code == 200:
            safe_title = (
                book["title"]
                .replace("/", "_")
                .replace("\\", "_")
                .replace(":", "_")[:40]
            )
            file_name = f"{safe_title}{book['ext']}"

            with open(file_name, "wb") as f:
              f.write(file_res.content)

            with open(file_name, "rb") as doc:
              bot.send_document(
                  message.chat.id,
                  doc,
                  caption=(
                      f"📖 *{book['title']}*\n✍️ Автор:"
                      f" `{book['author']}`\n🌐 Язык: `{book['lang']}`\n📁"
                      f" Формат: `{book['ext'].upper()[1:]}`"
                  ),
                  parse_mode="Markdown",
              )

            os.remove(file_name)
            sent_count += 1
        else:
          # Если это ссылка на карточку Open Library
          markup = types.InlineKeyboardMarkup()
          btn = types.InlineKeyboardButton(
              text="📥 Открыть страницу книги", url=book["url"]
          )
          markup.add(btn)
          bot.send_message(
              message.chat.id,
              f"📖 *{book['title']}*\n✍️ Автор: `{book['author']}`",
              parse_mode="Markdown",
              reply_markup=markup,
          )
          sent_count += 1
      except Exception as e:
        continue

    if sent_count == 0:
      bot.reply_to(
          message,
          "К сожалению, после тщательной проверки файлы для скачивания не"
          " обнаружены. Попробуй ввести название латиницей.",
      )
  else:
    bot.reply_to(
        message,
        "Ничего не удалось найти после проверки всех баз. Попробуй изменить"
        " запрос.",
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
