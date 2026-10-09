import { ArrowRight, CalendarDays, Clock3 } from "lucide-react";
import { Link } from "react-router-dom";
import type { Lesson } from "../../types";

export default function LessonCard({ lesson }: { lesson: Lesson }) {
  return (
    <article className="lesson-card">
      <div className="lesson-symbol">ƒ</div>
      <div className="lesson-info">
        <span className="subject-label">{lesson.subject}</span>
        <h3>{lesson.topic}</h3>
        <p>{lesson.teacher}</p>
        <div className="lesson-time">
          <span>
            <CalendarDays size={14} />
            {lesson.schedule}
          </span>
          <span>
            <Clock3 size={14} />
            {lesson.duration} мин
          </span>
        </div>
      </div>
      <Link to={`/lessons/${lesson.id}/chat`} className="button outline small">
        К уроку <ArrowRight size={16} />
      </Link>
    </article>
  );
}
