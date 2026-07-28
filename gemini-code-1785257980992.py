import telebot

TOKEN = '8887050197:AAF4SC3qXjsZaa7ARGLwKqM-S2ueF2cMjaM'

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот «Книжная полка» для поиска EPUB книг. Напиши мне название, и скоро я научусь его искать!")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    bot.send_message(message.chat.id, f"Ты ищешь: {message.text}\nПока что я только учусь, но скоро тут будет поиск по библиотекам!")

# Запуск бота
if __name__ == '__main__':
    print("Бот запускается...")
    bot.polling(none_stop=True)