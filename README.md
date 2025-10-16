# 🧩 Task Manager с Telegram-уведомлениями

Веб-приложение на **Django** для управления задачами с интеграцией **Telegram-бота**.  
Пользователи могут создавать списки задач, назначать исполнителей и получать уведомления как на сайте, так и в Telegram.

---

## 🚀 Возможности

- ✅ Регистрация и авторизация пользователей  
- ✅ Создание, редактирование и удаление задач  
- ✅ Назначение исполнителя и установка срока выполнения  
- ✅ Уведомления о новых и просроченных задачах:
  - через веб-интерфейс (встроенная система уведомлений);
  - через Telegram-бота
- ✅ Реальное обновление задач (**WebSocket через Django Channels**)  
- ✅ Автоматическая привязка Telegram-аккаунта к пользователю через токен  
- ✅ Фоновые уведомления с **Celery + Redis**

---

## 🧠 Технологии

| Компонент | Используемая библиотека |
|------------|--------------------------|
| 🖥️ Бэкенд | Django 3.2 |
| ⚙️ API | Django REST Framework |
| 🔄 Асинхронность | Django Channels |
| 🕐 Очереди задач | Celery + Redis |
| 🤖 Telegram | Aiogram 3 |
| 💾 База данных | SQLite (по умолчанию) |
| 🎨 Стили | Bootstrap 5 |
| 🔐 Авторизация | Кастомная модель пользователя (MyUser) |

---

## ⚙️ Установка и запуск проекта

### 1️⃣ Клонировать репозиторий

```bash
git clone https://github.com/<твой_профиль>/<repo_name>.git
cd <repo_name>

2️⃣ Установить зависимости
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)
pip install -r requirements.txt

3️⃣ Настроить переменные окружения

Создай файл .env в корне проекта и добавь туда:

TG_BOT_TOKEN=ВАШ_ТОКЕН_БОТА
TG_BOT_USERNAME=ИмяВашегоБотаБез@
API_BASE=http://127.0.0.1:8000


🧩 Telegram-бот создаётся через @BotFather

4️⃣ Применить миграции и создать суперпользователя
python manage.py migrate
python manage.py createsuperuser

5️⃣ Запустить Redis (локально)
redis-server

6️⃣ Запустить Celery и Django

Открой три терминала:

🖥️ Терминал 1 — Django сервер
python manage.py runserver

⚙️ Терминал 2 — Celery worker
celery -A task_manager worker -l info

⏰ Терминал 3 — Celery Beat (для периодических задач)
celery -A task_manager beat -l info

7️⃣ Запустить Telegram-бота
python bot.py

💬 Подключение Telegram

Зайди в свой профиль на сайте

Нажми кнопку 🤖 Подключить Telegram

Тебе будет показан персональный токен и ссылка

Перейди по ссылке и нажми Start в Telegram

🎉 Готово! Теперь уведомления о задачах будут приходить прямо в бот

📱 Основные команды бота
Команда	Назначение
/start <token>	Привязка аккаунта к сайту
/tasks	Просмотр активных задач
🏁 Нажать «Отметить выполненным»	Завершить задачу прямо из Telegram

👨‍💻 Автор

Александр Садуха
📧 Email: saduha94@mail.ru

🌐 GitHub: github.com/alexproevolution
