import { useState } from "react";
import { BASE } from "../../lib/api";
import { ArrowUpRight, BadgeCheck, Star } from "lucide-react";
import { Link } from "react-router-dom";
import type { Teacher } from "../../types";

export function TeacherAvatar({
  teacher,
  large = false,
  live = false,
}: {
  teacher: Teacher;
  large?: boolean;
  live?: boolean;
}) {
  const [failed, setFailed] = useState(false);
  return (
    <div
      className={`avatar ${teacher.color} ${large ? "large" : ""}`}
      aria-hidden="true"
    >
      {live && !failed && (
        <img
          src={`${BASE}/files/avatar/${teacher.id}`}
          alt=""
          onError={() => setFailed(true)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            position: "absolute",
            inset: 0,
            zIndex: 2,
            borderRadius: "inherit",
          }}
        />
      )}
      <span>{teacher.initials}</span>
      <div className="avatar-orbit" />
    </div>
  );
}
export default function TeacherCard({ teacher }: { teacher: Teacher }) {
  return (
    <article className="teacher-card">
      <div className="teacher-top">
        <TeacherAvatar teacher={teacher} />
        <span className="rating">
          <Star size={14} fill="currentColor" />
          {teacher.rating?.toFixed(1) ?? "—"}{" "}
          <small>({teacher.reviews_count})</small>
        </span>
      </div>
      <div className="subject-label">{teacher.subject}</div>
      <h3>
        <Link to={`/teachers/${teacher.id}`}>{teacher.name}</Link>
        {teacher.is_verified && (
          <BadgeCheck
            size={18}
            className="indigo"
            aria-label="Проверен (демо)"
          />
        )}
      </h3>
      <p>{teacher.tagline}</p>
      <div className="teacher-meta">
        Опыт: {teacher.experience} лет <span>·</span>{" "}
        {teacher.languages.join(" / ")}
      </div>
      <div className="teacher-bottom">
        <div>
          <strong>{teacher.price} сом</strong>
          <small> / 60 мин</small>
        </div>
        <Link
          className="round-link"
          to={`/teachers/${teacher.id}`}
          aria-label={`Профиль: ${teacher.name}`}
        >
          <ArrowUpRight size={21} />
        </Link>
      </div>
    </article>
  );
}
