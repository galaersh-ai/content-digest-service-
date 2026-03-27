"""
Telegram Bot for Content Digest Service
Принимает ссылки, ставит в очередь, возвращает результат.
"""
import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode

# Config
BOT_TOKEN = "8797609925:AAFnlaW2oFNhjlXwvA9d78doLuq5cmJaqLc"
DB_PATH = Path(__file__).parent / "data" / "queue.db"

# Init
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def init_db():
    """Initialize SQLite database."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            url TEXT,
            status TEXT DEFAULT 'pending',
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def add_task(user_id: int, url: str) -> int:
    """Add task to queue."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "INSERT INTO tasks (user_id, url) VALUES (?, ?)",
        [user_id, url]
    )
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return task_id


def get_pending_tasks():
    """Get all pending tasks."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    tasks = conn.execute(
        "SELECT * FROM tasks WHERE status = 'pending' ORDER BY created_at"
    ).fetchall()
    conn.close()
    return tasks


def get_task(task_id: int):
    """Get task by ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    task = conn.execute(
        "SELECT * FROM tasks WHERE id = ?", [task_id]
    ).fetchone()
    conn.close()
    return task


def update_task(task_id: int, status: str, result: str = None):
    """Update task status."""
    conn = sqlite3.connect(DB_PATH)
    if result:
        conn.execute(
            "UPDATE tasks SET status = ?, result = ?, completed_at = ? WHERE id = ?",
            [status, result, datetime.now(), task_id]
        )
    else:
        conn.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
            [status, task_id]
        )
    conn.commit()
    conn.close()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command."""
    await message.answer(
        "👋 Привет! Я делаю саммари контента.\n\n"
        "Отправь мне:\n"
        "• Ссылку на YouTube видео\n"
        "• Ссылку на статью\n\n"
        "Команды:\n"
        "/status - статус очереди\n"
        "/help - помощь"
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handle /help command."""
    await message.answer(
        "📖 **Как пользоваться:**\n\n"
        "1. Отправь ссылку на YouTube или статью\n"
        "2. Бот поставит задачу в очередь\n"
        "3. Когда готово — получишь саммари\n\n"
        "⏱ Обработка занимает 1-5 минут\n"
        "(зависит от длины видео)",
        parse_mode=ParseMode.MARKDOWN
    )


@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    """Show queue status."""
    tasks = get_pending_tasks()

    if not tasks:
        await message.answer("✅ Очередь пуста")
        return

    text = f"📋 В очереди: {len(tasks)} задач\n\n"
    for i, task in enumerate(tasks[:5], 1):
        url_short = task['url'][:40] + "..." if len(task['url']) > 40 else task['url']
        text += f"{i}. {url_short}\n"

    if len(tasks) > 5:
        text += f"\n...и ещё {len(tasks) - 5}"

    await message.answer(text)


@dp.message(F.text.regexp(r'https?://'))
async def handle_url(message: types.Message):
    """Handle URLs."""
    url = message.text.strip()

    # Validate URL
    is_youtube = "youtube.com" in url or "youtu.be" in url
    is_article = url.startswith("http")

    if not (is_youtube or is_article):
        await message.answer("❌ Отправь ссылку на YouTube или статью")
        return

    # Add to queue
    task_id = add_task(message.from_user.id, url)

    content_type = "🎬 YouTube" if is_youtube else "📄 Статья"
    await message.answer(
        f"{content_type} добавлен в очередь!\n\n"
        f"🆔 Задача #{task_id}\n"
        f"⏳ Статус: в очереди\n\n"
        f"Пришлю результат когда будет готово."
    )


@dp.message()
async def handle_other(message: types.Message):
    """Handle other messages."""
    await message.answer(
        "🤔 Не понял. Отправь ссылку на YouTube или статью.\n"
        "Или напиши /help"
    )


async def main():
    """Start bot."""
    init_db()
    print("🤖 Bot started!")
    print(f"📁 Database: {DB_PATH}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
