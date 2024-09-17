import os
import yt_dlp as youtube_dl  # Замена youtube-dl на yt-dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Задайте здесь ваш токен
TOKEN = 'your_token'

# Папка для временных файлов
DOWNLOAD_DIR = 'downloads'

# Идентификатор группы, куда нужно отправлять MP3-файлы
GROUP_CHAT_ID = 'id_group'  # Замените на ID вашей группы или ее юзернейм с @

# Функция для скачивания и конвертации видео
def download_and_convert(url: str):
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    ydl_opts = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        },
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '100',
        }],
        'noplaylist': True,  # Не скачивать плейлистов
        'socket_timeout': 300,  # Тайм-аут сокета (в секундах)
        'source_address': None,  # Можно указать IP-адрес, если у вас несколько сетевых интерфейсов
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).replace('.webm', '.mp3')
            
            # Проверим, какие файлы созданы в папке
            created_files = os.listdir(DOWNLOAD_DIR)
            print(f"Created files: {created_files}")  # Отладочный вывод списка файлов
            
            return filename
    except Exception as e:
        print(f"Error during download and conversion: {str(e)}")
        raise

# Функция для удаления всех файлов в папке downloads
def clean_downloads_dir():
    print("Cleaning downloads directory...")
    files = os.listdir(DOWNLOAD_DIR)
    if not files:
        print("No files to delete.")
    for filename in files:
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted {file_path}")
        except Exception as e:
            print(f"Error removing file {file_path}: {e}")

# Команда /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('Привет! Отправь мне ссылку на видео, и я конвертирую его в MP3.')

# Обработка входящих сообщений
async def handle_message(update: Update, context: CallbackContext):
    url = update.message.text

    if url.startswith('https://www.youtube.com/watch') or url.startswith('https://youtu.be/'):
        try:
            mp3_file = download_and_convert(url)
            print(f"Path to MP3 file: {mp3_file}")  # Отладочный вывод пути к файлу
            
            if os.path.exists(mp3_file):  # Проверьте, существует ли файл
                # Отправка файла в группу
                with open(mp3_file, 'rb') as audio:
                    await context.bot.send_audio(chat_id=GROUP_CHAT_ID, audio=audio)

                os.remove(mp3_file)

            else:
                await update.message.reply_text('Не удалось найти файл после скачивания.')
            
            # Очистка папки downloads
            clean_downloads_dir()
        except Exception as e:
            await update.message.reply_text(f'Произошла ошибка: {str(e)}')
    else:
        await update.message.reply_text('Пожалуйста, отправьте корректную ссылку на YouTube видео.')

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()
