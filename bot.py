import os
import time
import threading
import feedparser
import telebot
from dotenv import load_dotenv
from telebot.apihelper import ApiTelegramException

# Путь к файлу для сохранения ID отправленных новостей
SENT_NEWS_FILE = 'sent_news.txt'

def load_sent_news():
    if os.path.exists(SENT_NEWS_FILE):
        with open(SENT_NEWS_FILE, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f)
    return set()

def save_sent_news(news_id):
    with open(SENT_NEWS_FILE, 'a', encoding='utf-8') as f:
        f.write(news_id + '\n')

# Загрузка переменных окружения из .env
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# RSS-ленты новостей по ИИ
RSS_FEEDS = [
    'https://www.technologyreview.com/topic/artificial-intelligence/feed',
    'https://deepmind.com/blog/feed/basic',
    'https://openai.com/blog/rss/',
    'http://ai.googleblog.com/feeds/posts/default?alt=rss',
    'https://towardsdatascience.com/feed',
]

# Множество для отслеживания уже отправленных новостей
sent_news = load_sent_news()

# ID канала или чата для отправки новостей
CHAT_ID = '@intsring'

def fetch_and_send_news(feed_url):
    global sent_news
    try:
        feed = feedparser.parse(feed_url)
        # Отправляем посты в порядке от старых к новым
        for entry in reversed(feed.entries):
            news_id = entry.get('id') or entry.get('link')
            if news_id not in sent_news:
                title = entry.get('title', 'Новость без заголовка')
                link = entry.get('link', '')
                message = f"📰 {title}\nПодробнее: {link}"
                try:
                    bot.send_message(CHAT_ID, message)
                    sent_news.add(news_id)
                    save_sent_news(news_id)  # сохраняем ID нового поста
                except Exception as e:
                    print(f"Ошибка при отправке новости: {e}")
    except Exception as e:
        print(f"Ошибка при получении новостей: {e}")

def news_loop():
    while True:
        for feed_url in RSS_FEEDS:
            fetch_and_send_news(feed_url)
            time.sleep(600)  # Пауза 10 минут между проверками

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я буду присылать свежие новости об ИИ каждые 10 минут.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)

def run_bot():
    bot.delete_webhook()  # Удаляем webhook для избежания конфликтов
    while True:
        try:
            print("Запуск infinity_polling...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except ApiTelegramException as e:
            print(f"Ошибка Telegram API: {e}")
            if e.result.status_code == 409:
                print("Ошибка 409: другой экземпляр бота уже запущен.")
            time.sleep(10)
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
            time.sleep(10)

if __name__ == '__main__':
    threading.Thread(target=news_loop, daemon=True).start()
    print("Бот запущен")
    run_bot()
