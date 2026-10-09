import { CalendarDays, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";
import type { Teacher } from "../../types";

export default function BookingPanel({ teacher }: { teacher: Teacher }) {
  return (
    <aside className="panel booking-panel">
      <span className="eyebrow">ИНДИВИДУАЛЬНЫЙ УРОК</span>
      <h2>
        {teacher.price} сом <small>/ 60 мин</small>
      </h2>
      <div className="booking-detail">
        <CalendarDays size={20} />
        <p>
          Занятие онлайн<span>В Zoom, ссылка в чате урока</span>
        </p>
      </div>
      <div className="notice">
        Это демонстрационный профиль. Для бронирования выберите реальную услугу
        преподавателя.
      </div>
      <Link className="button full" to="/offers">
        Выбрать реальное занятие
      </Link>
      <Link className="button outline full" to="/presentation">
        Попробовать запись и переписку
      </Link>
      <Link to="/student" className="button outline full">
        Посмотреть кабинет ученика
      </Link>
      <p className="fine-print">
        <ShieldCheck size={14} />
        Комиссия платформы 10% включена в цену
      </p>
    </aside>
  );
}
