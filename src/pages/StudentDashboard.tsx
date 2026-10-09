import { Navigate, useLocation } from "react-router-dom";
import { ArrowUpRight, BookOpen, Check, Clock3, Target } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import DashboardLayout from "../components/layout/DashboardLayout";
import LiveDashboard from "../components/layout/LiveDashboard";
import LessonCard from "../components/lesson-card/LessonCard";
import AISummary from "../components/ai-summary/AISummary";
import RecordingPanel from "../components/ai-summary/RecordingPanel";
import { useAuth } from "../lib/auth";
import { DEMO_MODE } from "../lib/api";

export default function StudentDashboard() {
  const [done, setDone] = useState<number[]>([]);
  const { user } = useAuth();
  const { hash } = useLocation();
  if (hash === "#practice") return <Navigate to="/student/homework" replace />;
  if (hash === "#lessons") return <Navigate to="/student/lessons" replace />;
  return (
    <DashboardLayout>
      {user || !DEMO_MODE ? (
        <LiveDashboard />
      ) : (
        <>
          <div className="dashboard-heading">
            <div>
              <span className="eyebrow">КАЖДЫЙ ДЕНЬ — НЕМНОГО БЛИЖЕ</span>
              <h1>
                Привет, Азамат <span className="wave">✦</span>
              </h1>
              <p>Хороший день, чтобы разобраться в чём-то новом.</p>
            </div>
            <Link to="/catalog" className="button outline small">
              Найти преподавателя <ArrowUpRight size={16} />
            </Link>
          </div>
          <div className="goal-banner">
            <span className="goal-icon">
              <Target size={26} />
            </span>
            <div>
              <small>МОЯ ЦЕЛЬ · ПРИМЕР</small>
              <h3>Уверенно подготовиться к ОРТ</h3>
              <p>Математика · В своём темпе, с понятным планом</p>
            </div>
            <span className="goal-decoration">↗</span>
          </div>
          <div className="stats-grid">
            <div className="stat-card">
              <BookOpen size={19} />
              <strong>12</strong>
              <span>уроков в примере</span>
            </div>
            <div className="stat-card">
              <Check size={19} />
              <strong>{8 + done.length}</strong>
              <span>заданий выполнено</span>
            </div>
            <div className="stat-card">
              <Clock3 size={19} />
              <strong>3</strong>
              <span>темы для повторения</span>
            </div>
          </div>
          <section id="lessons">
            <div className="section-heading compact">
              <h2>Следующее занятие</h2>
              <span className="tag">Пример расписания</span>
            </div>
            <LessonCard
              lesson={{
                id: 1,
                subject: "Математика",
                topic: "Квадратные уравнения: закрепляем",
                teacher: "Айдана Токтосунова",
                schedule: "8 октября · 18:00 (Бишкек)",
                duration: 60,
              }}
            />
          </section>
          <div className="dashboard-columns">
            <section>
              <div className="section-heading compact">
                <h2>После прошлого урока</h2>
              </div>
              <AISummary />
            </section>
            <section id="practice">
              <div className="section-heading compact">
                <h2>Немного практики</h2>
                <span className="tag">{done.length}/3</span>
              </div>
              <div className="panel homework-panel">
                <p className="muted">
                  Демонстрационные отметки сохраняются до ухода со страницы.
                </p>
                {[
                  "Найти корни: x² − 5x + 6 = 0",
                  "Вычислить D: 2x² + 3x − 2 = 0",
                  "Повторить правило знаков",
                ].map((task, index) => (
                  <label
                    className={`homework-task ${done.includes(index) ? "done" : ""}`}
                    key={task}
                  >
                    <input
                      type="checkbox"
                      checked={done.includes(index)}
                      onChange={() =>
                        setDone((prev) =>
                          prev.includes(index)
                            ? prev.filter((i) => i !== index)
                            : [...prev, index],
                        )
                      }
                    />
                    <span>{task}</span>
                  </label>
                ))}
              </div>
            </section>
          </div>
          <RecordingPanel lessonId={1} />
          <Link className="button" to="/tutor">
            Открыть личный чат с тьютором
          </Link>
        </>
      )}
    </DashboardLayout>
  );
}
