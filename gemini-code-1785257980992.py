import os
import threading
from flask import Flask
import telebot

# Вставь свой токен Telegram-бота вместо кавычек
TOKEN = "8887050197:AAF4SC3qXjsZaa7ARGLwKqM-S2ueF2cMjaM"
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
  bot.reply_to(message, "Привет! Бот успешно запущен и работает.")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
  bot.reply_to(message, message.text)


# --- Веб-сервер Flask (обязателен для бесплатного тарифа Render) ---
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot is alive!"


def run_web():
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)


# Запуск веб-сервера в фоновом потоке
web_thread = threading.Thread(target=run_web)
web_thread.start()

# Запуск самого бота
if __name__ == "__main__":
  bot.infinity_polling()
