import { useAuth } from "../../lib/auth";
import type { ReactNode } from "react";
import {
  BookOpen,
  CalendarDays,
  GraduationCap,
  LayoutDashboard,
  Sparkles,
} from "lucide-react";
import { Link, NavLink } from "react-router-dom";

export default function DashboardLayout({
  children,
  teacher = false,
}: {
  children: ReactNode;
  teacher?: boolean;
}) {
  const { user } = useAuth();
  return (
    <div className="container dashboard-layout">
      <aside className="sidebar">
        <span className="eyebrow">ЛИЧНОЕ ПРОСТРАНСТВО</span>
        <nav aria-label="Разделы кабинета">
          <NavLink to="/student">Учусь</NavLink>
          <NavLink to={user ? "/teacher" : "/register"}>
            {user?.role === "teacher" ? "Преподаю" : "Стать преподавателем"}
          </NavLink>
          <NavLink end to={teacher ? "/teacher" : "/student"}>
            <LayoutDashboard size={18} />
            Обзор
          </NavLink>
          <Link to="/catalog">
            <GraduationCap size={18} />
            Преподаватели
          </Link>
          <NavLink to={teacher ? "/teacher/lessons" : "/student/lessons"}>
            <CalendarDays size={18} />
            Мои занятия
          </NavLink>
          <NavLink to={teacher ? "/teacher/homework" : "/student/homework"}>
            <BookOpen size={18} />
            {teacher ? "Домашние работы" : "Домашние задания"}
          </NavLink>
          <NavLink to="/tutor">
            <Sparkles size={18} />
            Тьютор и записи
          </NavLink>
          <NavLink to="/messages">Сообщения</NavLink>
          <NavLink to="/library">Заметки и практика</NavLink>
          <NavLink to="/notifications">Уведомления</NavLink>
          <NavLink to="/settings">Настройки профиля</NavLink>
          <NavLink to="/offers">Запись на урок</NavLink>
        </nav>
        <div className="sidebar-tip">
          <Sparkles size={24} />
          <h3>Учиться легче вместе</h3>
          <p>
            Персональный AI-тьютор поможет вернуться к важным моментам урока.
          </p>
          {teacher ? (
            <Link className="tag" to="/teacher">
              Подготовить урок
            </Link>
          ) : (
            <Link to="/tutor" className="tag">
              Задать вопрос тьютору
            </Link>
          )}
        </div>
      </aside>
      <div className="dashboard-content">{children}</div>
    </div>
  );
}
