import { useRef, useState } from "react";
import { uploadRecording } from "../../lib/recordings";
import { useAuth } from "../../lib/auth";
export default function RecordingUpload({
  lessonId,
  onSaved,
}: {
  lessonId: number;
  onSaved: () => void;
}) {
  const { token } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const id = useRef(crypto.randomUUID());
  async function upload() {
    if (!file || !consent) return;
    setBusy(true);
    setMessage("");
    try {
      await uploadRecording(
        lessonId,
        file,
        file.name.split(".").pop()?.toLowerCase() ?? "",
        id.current,
        token,
      );
      setMessage(
        file.name.toLowerCase().endsWith(".txt")
          ? "Текст сохранён. Анализ запущен."
          : "Запись сохранена. Транскрипция и анализ запущены.",
      );
      onSaved();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel spaced">
      <h2>Прикрепить запись урока к тьютору</h2>
      <p>
        Скачайте запись из Zoom на компьютер и выберите файл. MP4, M4A, MP3,
        WAV, WebM, OGG, FLAC — до 512 МБ и 60 минут; транскрипт TXT — до 300 КБ.
      </p>
      <p>
        Учитель или ученик могут загрузить запись своего урока. Ссылка Zoom сама
        по себе не является записью.
      </p>
      <input
        aria-label="Запись урока"
        type="file"
        accept=".mp4,.m4a,.mp3,.wav,.webm,.ogg,.flac,.txt"
        disabled={busy}
        onChange={(e) => {
          setFile(e.target.files?.[0] ?? null);
          id.current = crypto.randomUUID();
          setMessage("");
        }}
      />
      {file && <p>Выбран файл: {file.name}</p>}
      <label className="spaced">
        <input
          type="checkbox"
          checked={consent}
          onChange={(e) => setConsent(e.target.checked)}
          disabled={busy}
        />{" "}
        У меня есть согласие участников на сохранение записи и обработку аудио и
        текста в Groq.
      </label>
      <button
        className="button"
        disabled={busy || !file || !consent}
        onClick={() => void upload()}
      >
        {busy
          ? "Загружаем…"
          : file?.name.toLowerCase().endsWith(".txt")
            ? "Проанализировать текст и составить конспект"
            : "Транскрибировать и составить конспект"}
      </button>
      {message && <p role="status">{message}</p>}
    </section>
  );
}
