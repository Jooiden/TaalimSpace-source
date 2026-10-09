import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { AuthResponse } from "../types";

type Status = {
  ready: boolean;
  teacher_id: number;
  completed_lesson_id: number | null;
};

export default function Presentation() {
  const [status, setStatus] = useState<Status>();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { signIn, user } = useAuth();
  const navigate = useNavigate();
  useEffect(() => {
    api<Status>("/presentation/status")
      .then(setStatus)
      .catch((e) => setError(e.message));
  }, []);
  async function enter(role: "student" | "teacher") {
    setBusy(true);
    setError("");
    try {
      signIn(
        await api<AuthResponse>("/presentation/enter", {
          method: "POST",
          body: JSON.stringify({ role }),
        }),
      );
      navigate(role === "teacher" ? "/teacher" : "/catalog");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось войти");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="container page-section">
      <span className="eyebrow">AI ACADEMY · ПРЕЗЕНТАЦИЯ</span>
      <h1>Покажем весь путь обучения</h1>
      <p>
        Учебные аккаунты и материалы для хакатона. Бронирования, сообщения и
        ответы сохраняются в базе. Деньги не списываются.
      </p>
      <p className="notice">
        Этот вход доступен только на локальном компьютере. Для обычных
        пользователей есть <Link to="/register">регистрация</Link>. В одном
        браузере переключайте роль по очереди; для одновременного показа
        откройте второй браузер или приватное окно.
      </p>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      {!status && !error && <p role="status">Проверяем готовность…</p>}
      {status?.ready && (
        <>
          <div className="dashboard-columns">
            <section className="panel spaced">
              <h2>1. Я ученик</h2>
              <p>
                Выбрать услугу и время, записаться, написать преподавателю,
                сдать ДЗ и обсудить урок с тьютором.
              </p>
              <button
                className="button"
                disabled={busy}
                onClick={() => void enter("student")}
              >
                Войти как ученик
              </button>
            </section>
            <section className="panel spaced">
              <h2>2. Я преподаватель</h2>
              <p>
                Получить бронь, ответить ученику, отправить Zoom-ссылку, создать
                и проверить домашнее задание.
              </p>
              <button
                className="button outline"
                disabled={busy}
                onClick={() => void enter("teacher")}
              >
                Войти как преподаватель
              </button>
            </section>
          </div>
          {user && (
            <p>
              Сейчас: <strong>{user.name}</strong>.{" "}
              <Link to="/student">Учусь</Link> ·{" "}
              <Link to="/teacher">Преподаю</Link>
            </p>
          )}
          <section className="panel spaced">
            <h2>Сценарий на 5–7 минут</h2>
            <ol className="presentation-steps">
              <li>
                <strong>Каталог → запись.</strong> Войдите как ученик, выберите
                «Демо · Анна», услугу и свободное время. Откройте «Мои занятия»
                и чат нового урока.
              </li>
              <li>
                <strong>Переписка.</strong> Напишите вопрос. Вернитесь сюда,
                войдите как преподаватель, откройте тот же урок и ответьте.
                Передайте собственную ссылку Zoom.
              </li>
              <li>
                <strong>Услуги и расписание.</strong> В кабинете преподавателя
                покажите две цены, создание услуги и слота. Ученик может
                отменить или перенести будущую бронь.
              </li>
              <li>
                <strong>Материалы и ИИ.</strong>{" "}
                <Link to={`/tutor?lesson=${status.completed_lesson_id}`}>
                  Откройте подготовленный прошлый урок
                </Link>
                . Загрузите собственную запись либо учебный текст ниже. Текст
                проверяет анализ и конспект; распознавание речи показывайте на
                аудио/видео.
              </li>
              <li>
                <strong>Домашнее задание.</strong> В кабинете ученика сдайте
                ответ по прошлому уроку. Переключитесь на учителя и оставьте
                проверку. Затем можно поставить оценку преподавателю.
              </li>
              <li>
                <strong>Дополнительно.</strong> Покажите вложения в чате,{" "}
                <Link to="/messages">личные диалоги</Link>,{" "}
                <Link to="/notifications">напоминания</Link>, избранное,
                прогресс и <Link to="/library">заметки</Link>.
              </li>
            </ol>
            <a
              className="button outline"
              href="/presentation-lesson.txt"
              download
            >
              Скачать учебный транскрипт
            </a>{" "}
            <a
              className="button outline"
              href="/presentation-audio.wav"
              download
            >
              Скачать учебное аудио
            </a>
            <p>
              Аудио озвучено искусственным голосом: это вымышленный урок для
              проверки транскрипции.
            </p>
          </section>
          <section className="notice">
            <strong>Что обозначить жюри:</strong> урок проходит во внешнем Zoom;
            запись загружается вручную. ИИ требует подключения Groq и интернета.
            Подготовленный текст — вымышленный урок. Email, push и Stripe
            показываются как подключённые только после отдельной проверки
            доставки/оплаты.
          </section>
        </>
      )}
    </div>
  );
}
