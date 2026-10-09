import { api, DEMO_MODE } from "./api";

export type Finding = { topic: string; evidence: string; confidence: string };
export type Analysis = {
  source_quotes: string[];
  topic: string;
  summary: string;
  topics_covered: string[];
  understood: Finding[];
  difficult: Finding[];
  review_before_next: string[];
  insufficient_evidence: string;
  teacher_homework: { task: string; hint: string }[];
  extra_practice: { task: string; hint: string }[];
};
export type Recording = {
  id: string;
  lesson_id: number;
  status: string;
  stage: string;
  filename: string;
  created_at: string;
  error: string | null;
  duration: number | null;
  card: Analysis | null;
  transcript: string | null;
};
export const mediaQuery = (token?: string) => `demo=${DEMO_MODE && !token}`;
export const stages: Record<string, string> = {
  queued: "В очереди",
  extracting: "Извлекаем аудио",
  transcribing: "Распознаём речь",
  analyzing: "Готовим конспект и задания",
  publishing: "Сохраняем карточку",
  completed: "Карточка готова",
};

export async function uploadRecording(
  lessonId: number,
  file: Blob,
  extension: string,
  id: string,
  token?: string,
) {
  return api<Recording>(
    `/recordings/lesson/${lessonId}/${id}?${mediaQuery(token)}&extension=${encodeURIComponent(extension)}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/octet-stream" },
      body: file,
    },
    token,
  );
}

export async function downloadRecording(
  id: string,
  kind: "file" | "transcript",
  token?: string,
  filename = "recording.webm",
) {
  const base = (import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");
  const response = await fetch(
    `${base}/recordings/${id}/${kind}?${mediaQuery(token)}`,
    { headers: token ? { Authorization: `Bearer ${token}` } : {} },
  );
  if (!response.ok) throw new Error("Файл пока недоступен. Повторите позже.");
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download =
    kind === "transcript" ? "transcript.txt" : `lesson-${id}-${filename}`;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 60000);
}
