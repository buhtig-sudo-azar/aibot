import os
import time
import threading
import feedparser
import telebot
from dotenv import load_dotenv
from telebot.apihelper import ApiTelegramException

SENT_NEWS_FILE = 'sent_news.txt'

def load_sent_news():
    if os.path.exists(SENT_NEWS_FILE):
        with open(SENT_NEWS_FILE, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f)
    return set()

def save_sent_news(news_id):
    with open(SENT_NEWS_FILE, 'a', encoding='utf-8') as f:
        f.write(news_id + '\n')

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

RSS_FEEDS = [
    'https://www.technologyreview.com/topic/artificial-intelligence/feed',
    'https://deepmind.com/blog/feed/basic',
    'https://openai.com/blog/rss/',
    'http://ai.googleblog.com/feeds/posts/default?alt=rss',
    'https://towardsdatascience.com/feed',
]

sent_news = load_sent_news()

CHAT_ID = '@intsring'

# Храним для каждого источника индекс следующей новости для отправки
feed_next_indices = [0] * len(RSS_FEEDS)

def fetch_and_send_next_news():
    global sent_news, feed_next_indices
    for i, feed_url in enumerate(RSS_FEEDS):
        try:
            feed = feedparser.parse(feed_url)
            entries = feed.entries
            if feed_next_indices[i] < len(entries):
                entry = entries[feed_next_indices[i]]
                feed_next_indices[i] += 1
                news_id = entry.get('id') or entry.get('link')
                if news_id not in sent_news:
                    title = entry.get('title', 'Новость без заголовка')
                    link = entry.get('link', '')
                    message = f"📰 {title}\nПодробнее: {link}"
                    try:
                        bot.send_message(CHAT_ID, message)
                        sent_news.add(news_id)
                        save_sent_news(news_id)
                        print(f"Отправлена новость из ленты {i}: {title}")
                    except Exception as e:
                        print(f"Ошибка при отправке новости: {e}")
                else:
                    print(f"Новость уже отправлялась: {news_id}")
            else:
                print(f"Лента {i} закончилась, следующий индекс сброшен.")
                feed_next_indices[i] = 0  # сбросить индекс, чтобы начать заново
        except Exception as e:
            print(f"Ошибка при обработке ленты {feed_url}: {e}")

def news_loop():
    while True:
        fetch_and_send_next_news()
        time.sleep(600)  # Пауза 10 минут между рассылками

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я буду присылать свежие новости об ИИ каждые 10 минут.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)

def run_bot():
    bot.delete_webhook()
    while True:
        try:
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
