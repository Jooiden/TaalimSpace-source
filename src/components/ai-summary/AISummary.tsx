import { Check, Sparkles } from "lucide-react";

export default function AISummary() {
  return (
    <article className="ai-summary">
      <div className="section-heading">
        <span className="ai-label">
          <Sparkles size={17} />
          AI-конспект
        </span>
        <span className="tag">Пример результата</span>
      </div>
      <h3>Квадратные уравнения — по полочкам</h3>
      <p>
        На занятии разобрали дискриминант и научились находить корни квадратного
        уравнения.
      </p>
      <ul>
        <li>
          <Check size={16} />
          Общий вид: ax² + bx + c = 0
        </li>
        <li>
          <Check size={16} />
          Дискриминант: D = b² − 4ac
        </li>
        <li>
          <Check size={16} />
          Количество корней зависит от знака D
        </li>
      </ul>
      <div className="review-note">
        <strong>Стоит повторить</strong>
        <span>Знаки коэффициентов, когда перед x стоит минус.</span>
      </div>
    </article>
  );
}
