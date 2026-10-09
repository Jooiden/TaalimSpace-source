# Архитектура TaalimSpace

React/TypeScript/Vite → FastAPI → SQLAlchemy/PostgreSQL.
Groq используется только сервером для транскрипции и текстового анализа.
Zoom открывается по ссылке в отдельной вкладке; интеграции видеосвязи нет.

## Файлы
- src/pages: Home, Catalog, TeacherProfile, Offers, Login, Register,
  StudentDashboard, TeacherDashboard, LessonChat, TutorPage.
- src/components/booking: демонстрационная карточка записи, реальные услуги/слоты учителя.
- src/components/ai-tutor: чат тьютора, загрузка записи.
- src/components/ai-summary: результаты обработки и демонстрационный пример.
- src/components/lesson-card: карточка урока и сдача/проверка ДЗ.
- src/components/layout: навигация, live-кабинет.
- app/routers: auth, teachers, offers, booking, lessons, messages, recordings,
  tutor, homework, teacher, reviews, ai, files, notifications, directory, dialogs,
  library, progress, payments (только Stripe sandbox).
- app/services: авторизация, каталог, Groq, обработка файлов, очередь, контроль доступа,
  расчёт денежных долей.
- app/models и app/schemas: данные и проверка контрактов.
- migrations/versions: 0001 — базовая схема; 0002 — комментарии учителя и чат;
  0003 — сессии/услуги/файлы/уведомления; 0004 — Web Push; 0005 — диалоги/заметки.

## Дополнения API

- POST /api/auth/refresh, /logout: серверная сессия в HttpOnly-cookie, срок 30 дней.
- POST /api/auth/forgot-password, /reset-password: одноразовый токен на 30 минут;
  хранится SHA-256, смена пароля отзывает все сессии и access tokens.
- GET/POST /api/offers/mine/services, PATCH /{service_id}: несколько услуг.
- PATCH/DELETE /api/offers/mine/slots/{slot_id}: только свободные слоты;
  удаление слота с историей запрещено для сохранения связей.
- POST /api/lessons/{lesson_id}/cancel, /reschedule: до начала, только участники;
  перенос сохраняет услугу, цену и длительность.
- POST /api/files/avatar, /lesson/{id}; GET /avatar/{teacher_id}, /{file_id}:
  аватар публичен, файлы урока приватны. 5 МБ/10 МБ, 200 МБ на вложения аккаунта.
- GET/POST/PATCH /api/homework: учитель конкретного урока создаёт/редактирует задания;
  сданные и проверенные задания не изменяются этим методом.
- /api/notifications: inbox, preferences, read и push/key, push/subscribe, push/unsubscribe.
- /api/dialogs: диалоги между пользователем и преподавателем, сообщения и read.
- /api/directory: избранные, опубликованные услуги, отзывы.
- /api/library: собственные заметки и карточки (GET/POST/PATCH/DELETE).
- /api/progress и /students: агрегаты доступных уроков и работ.
- GET/PATCH /api/profile, GET /api/profile/time-zones: собственная необязательная
  дата рождения и часовой пояс IANA. Миграция 0006 добавляет nullable-поля User.
  Дата рождения не входит в публичную схему преподавателя. Время хранится в UTC,
  отображается и вводится в выбранном поясе; повторяющееся/пропущенное время DST
  отклоняется при вводе. Пока пояс не выбран — используется пояс браузера.
- /settings — настройки; /student/lessons и /teacher/lessons — занятия;
  /student/homework и /teacher/homework — задания. Старые ссылки с hash перенаправляются.
- /api/payments/checkout, /status/{id}, /webhook: только test mode, подпись и
  идемпотентное подтверждение. Отмена оплаченного тестового занятия ставит
  refund_required; автоматического возврата или выплат нет.

Бронирование/перенос/изменение слотов сериализуются по участникам. Цена и комиссия
фиксируются в Lesson. Расчёты Decimal. Для очереди и фоновых напоминаний пока один
процесс backend; внешний email может дублироваться при сбое после доставки до фиксации БД.

## Контракты
| Маршрут | Назначение |
| --- | --- |
| /api/auth/register, /login, /me | Аккаунты и роли |
| /api/teachers | Каталог примеров либо БД в зависимости от режима |
| /api/offers, /mine, /mine/slots, /{id}/slots | Реальные услуги и расписание |
| POST /api/booking | Бронь собственного аккаунта ученика |
| /api/lessons, /{id}/complete | История и завершение преподавателем |
| GET/POST /api/messages/{lesson_id} | Чат участников, сообщения и Zoom-ссылки |
| /api/recordings | Загрузка, этапы, повтор, скачивание |
| /api/tutor/personal, /chat, /demo/chat | Обзор своих уроков, конкретный урок, локальный пример |
| /api/homework | Задания, submit, feedback |
| /api/teacher/lesson-plan | AI-черновик плана |
| POST /api/reviews | Отзыв после завершённого урока |
| /api/payments/create-intent | Пока 501 |

## Хранение и доступ
PostgreSQL: пользователи, услуги, слоты, уроки, сообщения, карточки, ДЗ и отзывы.
MEDIA_DIR: оригинальные файлы, промежуточные этапы и очередь SQLite.
Это два разных хранилища; подключение PostgreSQL не переносит файлы автоматически.
Один backend-процесс до переноса очереди в общее хранилище.
Участника определяет серверный JWT, данные чужого урока недоступны.
Токен и история AI-чата живут в памяти страницы. Чат участников хранится в БД.

## Маршруты интерфейса
/lessons/:id/chat — чат и Zoom; /lessons/:id/room — только совместимый редирект.
/tutor?lesson=:id — загрузка записи, материалы и AI-обсуждение.
Демо-каталог может оставаться включённым при работе настоящих аккаунтов.
Для публичного развёртывания см. [DEPLOYMENT.md](DEPLOYMENT.md).

## Единый аккаунт

Регистрация: имя, email и пароль, без выбора роли. Каждый аккаунт может учиться. Раздел «Стать преподавателем» позволяет заполнить и опубликовать профиль через POST /api/offers/mine, затем добавить слоты. Это включает преподавание и сохраняет все возможности ученика. Кабинеты «Учусь / Преподаю» фильтруют уроки и ДЗ по участию; проверки и завершение доступны только преподавателю конкретного занятия. Поле role=teacher обозначает дополнительную возможность преподавать, а не запрет учиться.
