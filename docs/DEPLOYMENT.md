# Размещение TaalimSpace

## Быстрый бесплатный вариант для сдачи

Подготовлены Dockerfile и render.yaml. Можно разместить сайт и API на одном Render:
Vercel в этом варианте не нужен. Единый адрес устраняет зависимость входа от сторонних cookie.

1. GitHub → New repository → TaalimSpace → Private → Add README → Create.
2. Загрузить подготовленные исходники. Архив artifacts/TaalimSpace-source.zip нужно
   распаковать: в корне репозитория должны лежать Dockerfile, render.yaml, package.json,
   папки app и src. Сам ZIP вместо исходников Render не соберёт.
3. Render → New → Web Service → подключить этот репозиторий → Language: Docker →
   Instance Type: Free. Dockerfile уже содержит команды сборки и запуска.
4. В Environment добавить DATABASE_URL и GROQ_API_KEY из серверного .env;
   AUTH_SECRET — случайный секрет не короче 32 символов. Секреты в GitHub не загружать.
   DEMO_MODE=false, PRESENTATION_ENABLED=false, COOKIE_SECURE=true.
5. После получения адреса вида https://eduspace-xxxx.onrender.com задать:
   FRONTEND_URL=https://eduspace-xxxx.onrender.com и
   CORS_ORIGINS=["https://eduspace-xxxx.onrender.com"]. Дождаться перезапуска.
6. Для писем отдельно перенести BREVO_API_KEY и SMTP_FROM; восстановление пароля
   должно вести на публичный FRONTEND_URL, а не localhost.
7. Открыть /api/health, зарегистрироваться и пройти сценарий из RELEASE_READINESS.md.

Бесплатный диск временный: записи, фото, вложения и очередь не переживут перезапуск.
Не копировать туда локальную .media как замену постоянного хранилища. Бесплатный
сервер засыпает после простоя; первый запрос может ждать запуска.
Конфигурация подготовлена, но облачный Docker-build и доступность сайта ещё не проверены.
Дальше приведён прежний вариант с раздельными Render и Vercel.

## Аккаунты

Создайте самостоятельно аккаунты GitHub, Supabase, Render и Vercel.
Пароли, ключи и строку подключения не отправляйте в чат. Вход в панели выполняет владелец.
Обычный путь размещения: репозиторий GitHub → импорт проекта в Render и Vercel.

## PostgreSQL (Supabase)

1. Dashboard → New project, имя TaalimSpace, пароль базы, регион.
2. Дождитесь создания. Connect → URI → Session pooler для IPv4-подключения.
3. В серверном .env добавьте DATABASE_URL. Начало URI для SQLAlchemy:
   postgresql+psycopg:// вместо postgresql://. Подставьте пароль, специальные символы
   пароля закодируйте для URL. Не используйте публичный anon key вместо строки PostgreSQL.
4. Добавьте SSL-параметры согласно панели Supabase (обычно ?sslmode=require).
5. На отдельной базе примените: python -m alembic upgrade head.
6. Проверьте регистрацию ученика/учителя и бронирование.

SQLite — файл встроенной БД. PostgreSQL — отдельный сервер со своими файлами хранения;
нельзя заменить расширение файла SQLite и получить PostgreSQL. Основная БД приложения
настроена на PostgreSQL. Создание проекта Supabase и получение URI — шаг владельца.

## Render (backend)

Web Service → репозиторий, Python. Build: pip install -r requirements.txt.
Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT --no-proxy-headers.
Один процесс до переноса файловой очереди в общее хранилище.
Секреты в Environment: DATABASE_URL, AUTH_SECRET (случайные 32+ символа), GROQ_API_KEY.
Остальные настройки: DEMO_MODE=false, CORS_ORIGINS=["https://ваш-фронтенд.vercel.app"].
FRONTEND_URL=https://ваш-фронтенд.vercel.app, COOKIE_SECURE=true.
Перед реальным запуском выполните миграции, настройте постоянный MEDIA_DIR либо
перенесите хранение записей и очередь; по умолчанию они используют локальный диск.
Нельзя обещать сохранность файлов на временном диске хостинга.

## Vercel (frontend)

Import Git Repository → Vite. Build: pnpm build, Output: dist.
VITE_API_URL=https://ваш-backend.onrender.com/api.
VITE_DEMO_MODE=false для публичного запуска. Демо-каталог при желании остаётся
отдельной демонстрацией; нельзя публиковать локальные демо-endpoints.
vercel.json задаёт SPA fallback. Никакие секреты не помещать в VITE_*.

Для надёжного сохранения входа рекомендуется один origin: проксировать /api
через домен frontend на backend и оставить VITE_API_URL=/api. Если используются
разные домены Vercel/Render, HttpOnly-cookie с SameSite=None; Secure может блокироваться
браузером как сторонняя. Обязательно проверить refresh/logout на опубликованном сайте.
Адрес назначения прокси задавать только после получения действительного адреса Render.

## Письма и браузерные уведомления

Письма: [EMAIL_SETUP.md](EMAIL_SETUP.md). BREVO_API_KEY и SMTP_FROM — серверные настройки.
Push: VAPID_PRIVATE_KEY (секрет), VAPID_PUBLIC_KEY и VAPID_CONTACT=mailto:ваша-почта.
Нужен стабильный набор ключей и HTTPS (localhost разрешён для разработки).
Пользователь включает уведомления кнопкой в /notifications. Доставка на реальном
устройстве ещё не подтверждена. Если браузер не поддерживает Push, остаётся кабинет/email.
Фоновый процесс проверяет напоминания каждую минуту; остановка/сон хостинга задержит их.
Нельзя обещать точное время доставки на спящем бесплатном сервере.

## Тестовая оплата

Сейчас подключать Stripe необязательно: бронирование бесплатно. Для отдельного теста
нужны STRIPE_SECRET_KEY=sk_test_… и STRIPE_WEBHOOK_SECRET; webhook /api/payments/webhook.
Реальные ключи не включают оплату. Возвраты/выплаты не автоматизированы. Подключение
реальных платежей, поддержка страны и валюты требуют отдельного решения и проверки.

Видеоуроки открываются в Zoom; видеосервер и TURN для TaalimSpace не нужны.
Нынешняя версия не развёрнута. Перед запуском проверить PostgreSQL, два аккаунта,
чаты, приватность записей, квоты AI и файлов, ограничения регистрации и восстановление доступа.

Официальные инструкции:
- https://supabase.com/docs/guides/database/connecting-to-postgres
- https://render.com/docs/deploy-fastapi
- https://vercel.com/docs/frameworks/frontend/vite
