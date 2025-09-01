import os
from dotenv import load_dotenv
import telebot
import feedparser
import time
import threading

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

# Хранение уже отправленных новостей
sent_news = set()

# ID канала или чата для отправки новостей
CHAT_ID = '@intsring'  

def fetch_and_send_news(feed_url):
    global sent_news
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            news_id = entry.get('id') or entry.get('link')
            if news_id not in sent_news:
                title = entry.get('title', 'Новость без заголовка')
                link = entry.get('link', '')
                message = f"📰 {title}\nПодробнее: {link}"
                try:
                    bot.send_message(CHAT_ID, message)
                    sent_news.add(news_id)
                except Exception as e:
                    print(f"Ошибка при отправке новости: {e}")
    except Exception as e:
        print(f"Ошибка при получении новостей: {e}")


def news_loop():
    while True:
        for feed_url in RSS_FEEDS:
            fetch_and_send_news(feed_url)
            time.sleep(600)  # Пауза 10 минут между лентами


@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я буду присылать свежие новости об ИИ каждые 10 минут.")

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, message.text)

if __name__ == '__main__':
    threading.Thread(target=news_loop, daemon=True).start()
    bot.infinity_polling()
