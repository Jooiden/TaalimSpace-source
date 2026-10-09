import {
  ArrowLeft,
  BadgeCheck,
  Globe2,
  GraduationCap,
  Star,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import BookingPanel from "../components/booking/BookingPanel";
import { TeacherAvatar } from "../components/teacher-card/TeacherCard";
import { getTeacher } from "../lib/api";
import type { Teacher } from "../types";

export default function TeacherProfile() {
  const { id = "" } = useParams();
  const [teacher, setTeacher] = useState<Teacher | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setTeacher(null);
    setError("");
    getTeacher(id, controller.signal)
      .then((t) => {
        if (!controller.signal.aborted) setTeacher(t);
      })
      .catch((e: Error) => {
        if (!controller.signal.aborted) setError(e.message);
      });
    return () => controller.abort();
  }, [id]);
  return (
    <div className="container page-section">
      <Link className="text-link back-link" to="/catalog">
        <ArrowLeft size={17} />
        Все преподаватели
      </Link>
      {error ? (
        <div className="empty-state" role="alert">
          {error}
        </div>
      ) : !teacher ? (
        <div className="skeleton-card" aria-label="Загрузка профиля" />
      ) : (
        <div className="profile-layout">
          <div>
            <section className="panel profile-header">
              <TeacherAvatar teacher={teacher} large />
              <div>
                <span className="subject-label">{teacher.subject}</span>
                <h1>
                  {teacher.name}{" "}
                  {teacher.is_verified && <BadgeCheck className="indigo" />}
                </h1>
                <p>{teacher.tagline}</p>
                <div className="profile-badges">
                  <span>
                    <Star size={16} />
                    {teacher.rating ?? "Нет рейтинга"} · {teacher.reviews_count}{" "}
                    отзывов
                  </span>
                  <span>
                    <GraduationCap size={18} />
                    Опыт {teacher.experience} лет
                  </span>
                </div>
              </div>
            </section>
            <section className="panel profile-about">
              <h2>Давайте знакомиться</h2>
              <p>{teacher.bio}</p>
              <h3>
                <Globe2 size={19} />
                Языки обучения
              </h3>
              <div className="tags">
                {teacher.languages.map((l) => (
                  <span className="tag" key={l}>
                    {l}
                  </span>
                ))}
              </div>
              <h3>С чем я помогу</h3>
              <div className="tags">
                {teacher.subjects.map((s) => (
                  <span className="tag" key={s}>
                    {s}
                  </span>
                ))}
              </div>
            </section>
          </div>
          <BookingPanel teacher={teacher} />
        </div>
      )}
    </div>
  );
}
