import {
  ArrowUpRight,
  BookOpen,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Menu,
  Sparkles,
  X,
} from "lucide-react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { DEMO_MODE } from "../../lib/api";
import { useAuth } from "../../lib/auth";

export default function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { pathname } = useLocation();
  const { user, signOut } = useAuth();
  useEffect(() => {
    setMenuOpen(false);
    window.scrollTo(0, 0);
  }, [pathname]);
  return (
    <>
      <a className="skip-link" href="#main">
        К содержимому
      </a>
      <header className="site-header">
        <div className="container header-inner">
          <Link to="/" className="brand" aria-label="TaalimSpace — главная">
            <span className="brand-mark">
              <GraduationCap size={24} />
            </span>
            Taalim<span>Space</span>
            <i />
          </Link>
          <button
            className="icon-button mobile-menu"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label={menuOpen ? "Закрыть меню" : "Открыть меню"}
            aria-expanded={menuOpen}
          >
            {menuOpen ? <X /> : <Menu />}
          </button>
          <nav
            aria-label="Главное меню"
            className={menuOpen ? "main-nav open" : "main-nav"}
          >
            <NavLink to="/catalog">
              <BookOpen size={16} />
              Найти преподавателя
            </NavLink>
            <NavLink to="/student">
              <LayoutDashboard size={16} />
              Моё обучение
            </NavLink>
            <NavLink to="/offers">Записаться на урок</NavLink>
            <NavLink to={user ? "/teacher" : "/register"}>
              {user?.role === "teacher" ? "Преподаю" : "Стать преподавателем"}
            </NavLink>
          </nav>
          <div className="header-actions">
            {user ? (
              <button className="button ghost" onClick={signOut}>
                <LogOut size={16} />
                Выйти
              </button>
            ) : (
              <Link className="button small" to="/login">
                Войти <ArrowUpRight size={16} />
              </Link>
            )}
          </div>
        </div>
      </header>
      {DEMO_MODE && (
        <div className="demo-bar">
          <Sparkles size={14} />
          <span>
            Прототип AI Academy · Занятия проходят в Zoom. Бронирование без
            списаний. <Link to="/catalog?demo=1">Демо-каталог</Link>
            {" · "}
            <Link to="/presentation">Презентация: ученик / преподаватель</Link>
          </span>
        </div>
      )}
      <main id="main">
        <Outlet />
      </main>
      <footer className="site-footer container">
        <Link to="/" className="brand">
          <GraduationCap size={20} />
          TaalimSpace
        </Link>
        <span>Маленькие шаги. Большие открытия.</span>
        <span>Команда EduSpace · Хакатон AI Academy</span>
      </footer>
    </>
  );
}
