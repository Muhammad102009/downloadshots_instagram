import telebot
import os
import requests
from instaloader import Instaloader, Post
from urllib.parse import urlparse
from config import token

bot = telebot.TeleBot(token)

loader = Instaloader()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправь мне ссылку на видео из Instagram, и я попробую скачать его для тебя.")

@bot.message_handler(func=lambda message: True)
def download_instagram_video(message):
    url = message.text.strip()

    if "instagram.com" not in url:
        bot.reply_to(message, "Это не ссылка на Instagram. Попробуй другую ссылку.")
        return

    try:
        bot.reply_to(message, "Видео загружается, подожди немного...")

        url_path = urlparse(url).path
        shortcode = url_path.strip('/').split('/')[-1]  

        post = Post.from_shortcode(loader.context, shortcode)

        if not post.is_video:
            bot.reply_to(message, "Этот пост не содержит видео.")
            return

        video_url = post.video_url

        response = requests.get(video_url)
        if response.status_code != 200:
            bot.reply_to(message, "Не удалось загрузить видео. Попробуй позже.")
            return

        os.makedirs("./downloads", exist_ok=True)
        video_file = f"./downloads/{shortcode}.mp4"
        with open(video_file, "wb") as file:
            file.write(response.content)

        with open(video_file, 'rb') as video:
            bot.send_video(message.chat.id, video)

        os.remove(video_file)

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка при загрузке: {e}")

bot.polling()
