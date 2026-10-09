import { Navigate, useLocation } from "react-router-dom";
import { CalendarDays, Coins, Sparkles, Users } from "lucide-react";
import DashboardLayout from "../components/layout/DashboardLayout";
import LiveDashboard from "../components/layout/LiveDashboard";
import LessonCard from "../components/lesson-card/LessonCard";
import { useAuth } from "../lib/auth";
import { DEMO_MODE } from "../lib/api";

export default function TeacherDashboard() {
  const { user } = useAuth();
  const { hash } = useLocation();
  if (hash === "#practice") return <Navigate to="/teacher/homework" replace />;
  if (hash === "#lessons") return <Navigate to="/teacher/lessons" replace />;
  return (
    <DashboardLayout teacher>
      {user || !DEMO_MODE ? (
        <LiveDashboard teacher />
      ) : (
        <>
          <div className="page-intro">
            <span className="eyebrow">БОЛЬШЕ ВРЕМЕНИ НА ГЛАВНОЕ</span>
            <h1>Здравствуйте, Айдана</h1>
            <p>Ваши занятия, ученики и материалы — в одном пространстве.</p>
          </div>
          <div className="stats-grid">
            <div className="stat-card">
              <Users size={19} />
              <strong>8</strong>
              <span>учеников в примере</span>
            </div>
            <div className="stat-card">
              <CalendarDays size={19} />
              <strong>24</strong>
              <span>урока за демо-месяц</span>
            </div>
            <div className="stat-card">
              <Coins size={19} />
              <strong>
                12 960 <small>сом</small>
              </strong>
              <span>начисление в примере</span>
            </div>
          </div>
          <section id="lessons">
            <div className="section-heading compact">
              <h2>Расписание</h2>
              <span className="tag">Демонстрационные занятия</span>
            </div>
            <LessonCard
              lesson={{
                id: 1,
                subject: "Математика",
                topic: "Квадратные уравнения",
                teacher: "Ученик: Азамат",
                schedule: "8 октября · 18:00 (Бишкек)",
                duration: 60,
              }}
            />
          </section>
          <div className="dashboard-columns spaced">
            <section className="panel">
              <h2>Прозрачные начисления</h2>
              <p>Пример расчёта: 24 урока × 600 сом</p>
              <div className="earning-row">
                <span>Стоимость уроков</span>
                <strong>14 400 сом</strong>
              </div>
              <div className="earning-row">
                <span>Комиссия TaalimSpace · 10%</span>
                <strong>1 440 сом</strong>
              </div>
              <div className="earning-row total">
                <span>Доля преподавателя</span>
                <strong>12 960 сом</strong>
              </div>
              <p className="fine-print">
                Это пример учёта, а не совершённая выплата.
              </p>
            </section>
            <section id="practice" className="panel teacher-ai">
              <Sparkles size={30} />
              <h2>Ваш помощник в подготовке</h2>
              <p>
                AI поможет составить план, предложить практику и собрать
                трудности ученика перед следующим занятием.
              </p>
              <span className="tag">Интеграция Groq — следующий этап</span>
            </section>
          </div>
        </>
      )}
    </DashboardLayout>
  );
}
