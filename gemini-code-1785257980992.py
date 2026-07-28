import os
import random
import threading
import time
from urllib.parse import quote
from bs4 import BeautifulSoup
from flask import Flask
import requests
import telebot
from telebot import types

TOKEN = "8887050197:AAF4SC3qXjsZaa7ARGLwKqM-S2ueF2cMjaM"
bot = telebot.TeleBot(TOKEN)

TARGET_CHAT_ID = None

RECORD_CHANNELS = {
    "Big Hits": "bh",
    "Гоп FM": "gop",
    "Trap": "trap",
    "Neurofunk": "neurofunk",
}


def get_current_record_track(channel_key):
  """Залезает на Radio Record и забирает трек из эфира"""
  try:
    url = "https://www.radiorecord.ru/api/stations/"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
      data = response.json()
      stations = data.get("result", {}).get("stations", [])
      for station in stations:
        if station.get("alias") == channel_key:
          track = station.get("track", {})
          artist = track.get("artist", "")
          title = track.get("title", "")
          if artist and title:
            return f"{artist} - {title}"
  except Exception:
    pass
  return None


def get_topradio_chart():
  """Парсит топ-20 с сайта TopRadio (tv3.lv)"""
  tracks = []
  try:
    url = "https://tv3.lv/topradio/ru/top20/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
      soup = BeautifulSoup(response.text, "html.parser")
      # Ищем элементы с треками (структура сайта может содержать блоки песен)
      # Универсальный поиск исполнителей и названий на странице чарта
      items = soup.select(".track, .song-item, tr, li")
      for item in items:
        text = item.get_text(separator=" ", strip=True)
        if "-" in text and len(text) < 100:
          tracks.append(text)
      # Если спарсилось слишком много или мало, вернем случайный выбор или фолбек
      if tracks:
        return random.choice(tracks)
  except Exception:
    pass
  return None


@bot.message_handler(commands=["start"])
def send_welcome(message):
  global TARGET_CHAT_ID
  TARGET_CHAT_ID = message.chat.id
  bot.reply_to(
      message,
      "🎵 Музыкальный пульт обновлен!\n\n"
      "📻 *Расписание и эфир:*\n"
      "• **12:00 – 14:00 (Дневной микс):** Radio Record & Рэп\n"
      "• **17:00 (Ежедневно):** Топ-чарты русской попсы\n"
      "• **Пятница в 19:00:** 🏆 Топ-20 от TopRadio (tv3.lv)\n"
      "• **22:00 – 23:00:** Тяжелый метал и рок-баллады\n\n"
      "🎸 Пишите любой запрос в чат в любой момент!",
      parse_mode="Markdown",
  )


def send_music_batch(chat_id, genre_key, title_prefix):
  if not chat_id:
    return
  try:
    query = ""
    if genre_key == "day_mix":
      sub_mode = random.choice(["live_radio", "top_rated_rap", "new_releases"])
      if sub_mode == "live_radio":
        channel_name, channel_code = random.choice(
            list(RECORD_CHANNELS.items())
        )
        live_track = get_current_record_track(channel_code)
        if live_track:
          query = live_track
          title_prefix = f"🔥 Radio Record ({channel_name}) [Live]"
        else:
          query = f"Radio Record {channel_name} top hits"
      elif sub_mode == "top_rated_rap":
        query = random.choice([
            "Russian rap top rated",
            "German rap hit tracks",
            "English hip hop best rating",
        ])
        title_prefix = "⭐ Высокий рейтинг: Рэп микс"
      else:
        query = random.choice([
            "Electronic dance music new releases",
            "Trap music fresh hits",
        ])
        title_prefix = "⚡ Свежие новинки электроники"

    elif genre_key == "pop_charts":
      query = random.choice([
          "Русские поп чарты топ рейтинг",
          "Популярные песни новинки недели",
      ])
    elif genre_key == "heavy_metal":
      query = random.choice([
          "Melodic heavy metal top tracks",
          "Symphonic metal best ballad",
      ])
    elif genre_key == "topradio_chart":
      # Пытаемся взять трек с TopRadio, если не выйдет — берем общие хиты чарта
      top_track = get_topradio_chart()
      if top_track:
        query = top_track
        title_prefix = "🏆 TopRadio Top 20 (tv3.lv)"
      else:
        query = "TopRadio hit chart 2026"
        title_prefix = "🏆 TopRadio Top 20"

    encoded = quote(f"{query} music")
    yt_music = f"https://music.youtube.com/search?q={encoded}"
    yt_video = f"https://www.youtube.com/results?search_query={encoded}"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(text="🎧 Слушать в YouTube Music", url=yt_music)
    )
    markup.add(
        types.InlineKeyboardButton(text="📺 Смотреть на YouTube", url=yt_video)
    )

    text = (
        f"🎶 *{title_prefix}*\n\n🎯 Трек / Черт: `{query}`\nПодборка готова!"
    )
    bot.send_message(
        chat_id, text, parse_mode="Markdown", reply_markup=markup
    )
  except Exception:
    pass


def schedule_worker():
  global TARGET_CHAT_ID
  last_day_sent = -1
  last_pop_sent = -1
  last_metal_sent = -1
  last_topradio_sent = -1

  while True:
    try:
      current_time = time.localtime()
      weekday = current_time.tm_wday  # 4 это пятница
      hour = current_time.tm_hour
      minute = current_time.tm_min
      day = current_time.tm_mday

      if TARGET_CHAT_ID:
        # Пятничный топ в 19:00 с TopRadio (tv3.lv/topradio/ru/top20/)
        if weekday == 4 and hour == 19 and minute < 5 and last_topradio_sent != day:
          send_music_batch(TARGET_CHAT_ID, "topradio_chart", "🏆 TopRadio Top 20")
          last_topradio_sent = day
          time.sleep(300)

        # Дневной микс (с 12:00 до 14:00)
        elif 12 <= hour < 14 and last_day_sent != day:
          send_music_batch(
              TARGET_CHAT_ID,
              "day_mix",
              "☀️ Дневной микс (Radio Record & Рэп)",
          )
          last_day_sent = day
          time.sleep(3600)

        # Вечерний поп-чарт (в 17:00)
        elif hour == 17 and minute < 5 and last_pop_sent != day:
          send_music_batch(
              TARGET_CHAT_ID, "pop_charts", "🌙 Вечерние топ-чарты русской попсы"
          )
          last_pop_sent = day
          time.sleep(300)

        # Ночной тяжелый метал (с 22:00 до 23:00)
        elif 22 <= hour < 23 and last_metal_sent != day:
          send_music_batch(
              TARGET_CHAT_ID,
              "heavy_metal",
              "🎸 Ночной тяжелый метал и рок-баллады",
          )
          last_metal_sent = day
          time.sleep(3600)

    except Exception:
      pass

    time.sleep(30)


@bot.message_handler(func=lambda message: True)
def handle_user_query(message):
  global TARGET_CHAT_ID
  TARGET_CHAT_ID = message.chat.id

  query = message.text.strip()
  if not query:
    return

  try:
    encoded = quote(f"{query} music")
    yt_music = f"https://music.youtube.com/search?q={encoded}"
    yt_video = f"https://www.youtube.com/results?search_query={encoded}"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(text="🎧 Слушать в YouTube Music", url=yt_music)
    )
    markup.add(
        types.InlineKeyboardButton(text="📺 Смотреть на YouTube", url=yt_video)
    )

    bot.send_message(
        message.chat.id,
        f"🎸 *Музыка по вашему запросу:* `{query}`",
        parse_mode="Markdown",
        reply_markup=markup,
    )
  except Exception:
    bot.send_message(
        message.chat.id, "Не удалось выполнить поиск. Попробуйте еще раз."
    )


# --- Веб-сервер Flask (для Render) ---
app = Flask(__name__)


@app.route("/")
def home():
  return "Music Bot is alive!"


def run_web():
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
  web_thread = threading.Thread(target=run_web)
  web_thread.start()

  sched_thread = threading.Thread(target=schedule_worker, daemon=True)
  sched_thread.start()

  bot.infinity_polling()
