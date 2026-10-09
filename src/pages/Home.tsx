import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Check,
  CheckCheck,
  ChevronRight,
  GraduationCap,
  Play,
  Sparkles,
  Target,
} from "lucide-react";
import { Link } from "react-router-dom";
import TeacherCard from "../components/teacher-card/TeacherCard";
import teachers from "../../shared/demo-teachers.json";
import { DEMO_MODE } from "../lib/api";

export default function Home() {
  return (
    <>
      <section className="container hero">
        <div className="hero-copy">
          <span className="pill">
            <span className="pulse-dot" />
            Живые преподаватели. Умная поддержка.
          </span>
          <h1>
            Твоё пространство
            <br />
            для{" "}
            <span className="highlight">
              больших
              <br className="desktop-break" /> открытий.
            </span>
          </h1>
          <p className="hero-description">
            Найди своего преподавателя, занимайся онлайн
            <br className="desktop-break" /> и двигайся к цели с персональным
            AI-тьютором.
          </p>
          <div className="hero-actions">
            <Link to="/catalog" className="button">
              Найти преподавателя <ArrowUpRight size={19} />
            </Link>
            <Link to="/student" className="text-link">
              <span className="play-icon">
                <Play size={13} fill="currentColor" />
              </span>
              Как это работает
            </Link>
          </div>
          <div className="hero-footnotes">
            <span>
              <Check size={15} />В твоём темпе
            </span>
            <span>
              <Check size={15} />
              Под твою цель
            </span>
            <span>
              <Check size={15} />В одном месте
            </span>
          </div>
        </div>
        <div className="hero-art" aria-label="Пример учебного пространства">
          <div className="art-orbit orbit-one" />
          <div className="art-orbit orbit-two" />
          <div className="floating-symbol symbol-one">π</div>
          <div className="floating-symbol symbol-two">Aa</div>
          <div className="art-main">
            <div className="art-top">
              <span className="mini-logo">
                <GraduationCap size={19} />
              </span>
              <span>Твоя следующая маленькая победа</span>
              <span className="art-dot" />
            </div>
            <div className="art-chalkboard">
              <span>МАТЕМАТИКА · ПРИМЕР УРОКА</span>
              <div className="chalk-formula">x² − 5x + 6 = 0</div>
              <div className="formula-note">
                Всё сложное начинается с простого.
              </div>
              <div className="chalk-decoration">ƒ</div>
            </div>
            <div className="art-bottom">
              <div className="tiny-avatar">АТ</div>
              <div>
                <strong>Айдана Токтосунова</strong>
                <small>Твой преподаватель математики</small>
              </div>
              <span className="art-video">
                <Play size={15} fill="currentColor" />
              </span>
            </div>
          </div>
          <div className="floating-note note-ai">
            <span className="sparkle-box">
              <Sparkles size={22} />
            </span>
            <div>
              <strong>Урок закончился. Поддержка — нет.</strong>
              <p>Конспект, практика и помощь AI-тьютора</p>
            </div>
          </div>
          <div className="floating-note note-progress">
            <div className="progress-icon">
              <CheckCheck size={22} />
            </div>
            <div>
              <strong>Ещё одна тема понятна</strong>
              <p>Маленький шаг к большой цели</p>
            </div>
          </div>
          <span className="art-caption">
            Будущее обучения — рядом с тобой ✦
          </span>
        </div>
      </section>
      <section className="subject-strip">
        <div className="container">
          <span>Что будем изучать?</span>
          {[
            "Математика",
            "Английский",
            "Физика",
            "Подготовка к ОРТ",
            "Кыргызский язык",
          ].map((subject, i) => (
            <Link
              key={subject}
              to={`/catalog?subject=${encodeURIComponent(subject)}`}
            >
              <span>{["∑", "Aa", "⚛", "↗", "Ө"][i]}</span>
              {subject}
              <ChevronRight size={14} />
            </Link>
          ))}
        </div>
      </section>
      <section className="container section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">ОБРАЗОВАНИЕ С ЧЕЛОВЕЧЕСКИМ ЛИЦОМ</span>
            <h2>Свой преподаватель меняет всё</h2>
            <p>Выбирай по предмету, языку и подходу к обучению.</p>
          </div>
          <Link to="/catalog" className="text-link">
            Весь каталог <ArrowRight size={18} />
          </Link>
        </div>
        {DEMO_MODE ? (
          <div className="teacher-grid">
            {teachers.slice(0, 3).map((t) => (
              <TeacherCard key={t.id} teacher={t} />
            ))}
          </div>
        ) : (
          <div className="panel">
            <p>Посмотрите доступных преподавателей в каталоге.</p>
            <Link className="button" to="/catalog">
              Открыть каталог
            </Link>
          </div>
        )}
      </section>
      <section className="container journey-section">
        <div className="journey-heading">
          <span className="eyebrow">БОЛЬШЕ, ЧЕМ ПРОСТО УРОКИ</span>
          <h2>
            У обучения есть
            <br />
            продолжение.
          </h2>
          <p>
            Преподаватель помогает на занятии.
            <br />
            AI-тьютор — между встречами.
          </p>
          <Link to="/student" className="text-link">
            Заглянуть в кабинет <ArrowUpRight size={18} />
          </Link>
        </div>
        <div className="journey-steps">
          {[
            {
              icon: Target,
              title: "Найди своего преподавателя",
              text: "Предмет, язык и бюджет — выбери то, что подходит тебе.",
            },
            {
              icon: BookOpen,
              title: "Разберись на живом уроке",
              text: "Задавай вопросы и решай задачи вместе с преподавателем.",
            },
            {
              icon: Sparkles,
              title: "Закрепи с AI-тьютором",
              text: "Возвращайся к конспекту и практикуйся в своём темпе.",
            },
          ].map(({ icon: Icon, title, text }, i) => (
            <div className="journey-step" key={title}>
              <div className="step-icon">
                <Icon size={23} />
              </div>
              <div>
                <span>0{i + 1}</span>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
