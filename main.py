import telebot
import os
import requests
from instaloader import Instaloader, Post
from pytube import YouTube
from urllib.parse import urlparse
import tempfile
from config import token

bot = telebot.TeleBot(token)

loader = Instaloader()

# Функция для скачивания видео с TikTok
def get_tiktok_video(url):
    try:
        # Используем ttdownloader.com для получения ссылки на видео
        api_url = "https://ttdownloader.com/"
        session = requests.Session()
        
        # Отправляем POST-запрос
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0"
        }
        data = {"url": url}
        response = session.post(api_url, headers=headers, data=data)

        if response.status_code != 200:
            return None

        # Ищем прямую ссылку на видео
        video_url_start = response.text.find('href="') + 6
        video_url_end = response.text.find('"', video_url_start)
        video_url = response.text[video_url_start:video_url_end]

        if not video_url or not video_url.startswith("http"):
            return None

        return video_url
    except Exception as e:
        print(f"Ошибка при извлечении видео TikTok: {e}")
        return None

# Функция для скачивания видео с YouTube
def get_youtube_video(url):
    try:
        # Пытаться загрузить видео с YouTube с использованием pytube
        yt = YouTube(url)
        
        # Получаем поток с наивысшим качеством
        stream = yt.streams.filter(progressive=True, file_extension='mp4').get_highest_resolution()

        # Скачиваем видео в файл
        video_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        stream.download(output_path=os.path.dirname(video_file.name), filename=video_file.name)

        return video_file.name
    except Exception as e:
        print(f"Ошибка при извлечении видео YouTube: {e}")
        return None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправь мне ссылку на видео из Instagram, TikTok или YouTube, и я попробую скачать его для тебя.")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text.strip()

    if "instagram.com" in url:
        # Логика для скачивания видео с Instagram
        try:
            bot.reply_to(message, "Видео загружается с Instagram, подожди немного...")

            url_path = urlparse(url).path
            shortcode = url_path.strip('/').split('/')[-1]  

            post = Post.from_shortcode(loader.context, shortcode)

            if not post.is_video:
                bot.reply_to(message, "Этот пост не содержит видео.")
                return

            video_url = post.video_url

            response = requests.get(video_url)
            if response.status_code != 200:
                bot.reply_to(message, "Не удалось загрузить видео из Instagram. Попробуй позже.")
                return

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name

            with open(temp_file_path, 'rb') as video:
                bot.send_video(message.chat.id, video)

            os.remove(temp_file_path)

        except Exception as e:
            bot.reply_to(message, f"Произошла ошибка при загрузке видео из Instagram: {e}")

    elif "tiktok.com" in url:
        # Логика для скачивания видео с TikTok
        try:
            bot.reply_to(message, "Видео загружается с TikTok, подожди немного...")
            video_url = get_tiktok_video(url)

            if not video_url:
                bot.reply_to(message, "Не удалось извлечь ссылку на видео с TikTok. Попробуй позже.")
                return

            response = requests.get(video_url)
            if response.status_code != 200:
                bot.reply_to(message, "Не удалось загрузить видео с TikTok. Попробуй позже.")
                return

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name

            with open(temp_file_path, 'rb') as video:
                bot.send_video(message.chat.id, video)

            os.remove(temp_file_path)

        except Exception as e:
            bot.reply_to(message, f"Произошла ошибка при загрузке видео из TikTok: {e}")

    elif "youtube.com" in url or "youtu.be" in url:
        # Логика для скачивания видео с YouTube
        try:
            bot.reply_to(message, "Видео загружается с YouTube, подожди немного...")
            video_file_path = get_youtube_video(url)

            if not video_file_path:
                bot.reply_to(message, "Не удалось извлечь ссылку на видео с YouTube. Попробуй позже.")
                return

            with open(video_file_path, 'rb') as video:
                bot.send_video(message.chat.id, video)

            os.remove(video_file_path)

        except Exception as e:
            bot.reply_to(message, f"Произошла ошибка при загрузке видео с YouTube: {e}")

    else:
        bot.reply_to(message, "Это не ссылка на Instagram, TikTok или YouTube. Попробуй другую ссылку.")

bot.polling()
