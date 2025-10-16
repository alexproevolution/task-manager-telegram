
import os
import logging
import aiohttp
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

load_dotenv()

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
API_BASE = os.getenv('API_BASE', 'http://127.0.0.1:8000')

if not BOT_TOKEN:
    raise RuntimeError("TG_BOT_TOKEN env variable is not set")

bot = Bot(token=BOT_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot)


async def post_json(session, url, json_payload):
    """Отправляет POST-запрос с JSON и возвращает (status, json)."""
    async with session.post(url, json=json_payload, timeout=10) as resp:
        try:
            data = await resp.json()
        except Exception:
            data = {}
        return resp.status, data


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    """Привязка Telegram аккаунта через команду /start <token>."""
    args = message.get_args()
    chat_id = str(message.chat.id)

    async with aiohttp.ClientSession() as session:
        if args:
            url = f"{API_BASE}/tasks/api/bot/link/"
            payload = {'token': args, 'chat_id': chat_id}
            status, data = await post_json(session, url, payload)

            if status == 200:
                await message.answer(
                    "✅ Аккаунт успешно привязан!\n"
                    "Теперь вы будете получать уведомления о задачах."
                )
            else:
                detail = data.get('detail') if isinstance(data, dict) else None
                await message.answer(f"❌ Ошибка привязки: {detail or status}")
        else:
            await message.answer(
                "👋 Привет!\n"
                "Чтобы привязать аккаунт — сгенерируйте токен в веб-интерфейсе "
                "и выполните:\n\n<code>/start &lt;токен&gt;</code>"
            )


@dp.message_handler(commands=['tasks'])
async def tasks_handler(message: types.Message):
    """Вывод списка активных задач пользователя."""
    chat_id = str(message.chat.id)
    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE}/tasks/api/bot/tasks_by_chat/?chat_id={chat_id}"
        async with session.get(url, timeout=10) as resp:
            if resp.status != 200:
                await message.answer("⚠️ Не удалось получить список задач.")
                return
            data = await resp.json()

    if not data:
        await message.answer("🎉 У вас нет открытых задач.")
        return

    for task in data:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(
                "✅ Отметить выполненной",
                callback_data=f"done:{task['id']}"
            )
        )
        txt = (
            f"<b>{task['title']}</b>\n"
            f"#ID: {task['id']}\n"
            f"Срок: {task.get('due_date') or '—'}\n\n"
            f"{task.get('description') or ''}"
        )
        await message.answer(txt, reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('done:'))
async def cb_done(callback_query: types.CallbackQuery):
    """Обработчик кнопки 'Отметить выполненной'."""
    task_id = callback_query.data.split(':', 1)[1]
    chat_id = str(callback_query.message.chat.id)

    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE}/tasks/api/bot/complete_by_chat/"
        payload = {'chat_id': chat_id, 'task_id': task_id}
        status, data = await post_json(session, url, payload)

        if status == 200:
            await callback_query.answer("✅ Задача отмечена как выполненная!")
            await bot.edit_message_reply_markup(
                chat_id=callback_query.from_user.id,
                message_id=callback_query.message.message_id,
                reply_markup=None
            )
        else:
            error = data.get('detail', 'unknown')
            await callback_query.answer(f"❌ Ошибка: {error}", show_alert=True)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
