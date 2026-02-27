import os
import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from google.colab import drive

# 1. ПРИВЯЗКА К ГУГЛ ДИСКУ (stanislavsfiral@gmail.com)
drive.mount('/content/drive')

# Путь к папке управления системой на Диске
GIDEON_CLOUD_PATH = "/content/drive/MyDrive/GIDEON_ARCHIVE/"
if not os.path.exists(GIDEON_CLOUD_PATH):
    os.makedirs(GIDEON_CLOUD_PATH)

DB_FILE = os.path.join(GIDEON_CLOUD_PATH, "brain.txt")
STATS_FILE = os.path.join(GIDEON_CLOUD_PATH, "queries_stats.log")

def log_to_cloud(user, text):
    """Сбор статистики запросов на Диск"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] ID:{user.id} Username:{user.username} -> Query: {text}\n"
    with open(STATS_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

def load_cloud_library():
    """Загрузка знаний из библиотеки на Диске"""
    memory = {}
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            f.write("стабильный ноль : Это центр баланса в системе GIDEON.\n---\n")
    
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            blocks = f.read().split("---")
            for block in blocks:
                if ":" in block:
                    k, v = block.split(":", 1)
                    memory[k.strip().lower()] = v.strip()
    except Exception as e:
        print(f"Ошибка библиотеки: {e}")
    return memory

async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    user = update.effective_user
    query = update.message.text
    
    # Сбор статистики
    log_to_cloud(user, query)
    
    # Поиск ответа
    library = load_cloud_library()
    query_lower = query.lower()
    
    response = None
    for key, answer in library.items():
        if key in query_lower:
            response = answer
            break 

    if not response:
        response = library.get("стабильный ноль", "Система GIDEON: Стабильный Ноль.")

    await update.message.reply_text(f"🌀 GIDEON (Library Mode):\n{response}")

# Твой токен остается прежним
TOKEN = "8642821622:AAEXYAWcj-BwMXQYl9sTClhEmF-t9X80I84"

def start_engine():
    print(f"🚀 GIDEON запущен. Статистика пишется в: {STATS_FILE}")
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_response))
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    start_engine()
