import type {
  AuthResponse,
  CatalogFilters,
  Teacher,
  TeacherPage,
} from "../types";
import demoTeachers from "../../shared/demo-teachers.json";

export const DEMO_MODE = import.meta.env.VITE_DEMO_MODE !== "false";
export const BASE = (import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type"))
    headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${BASE}${path}`, {
    ...options,
    credentials: "include",
    headers,
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: unknown;
    } | null;
    throw new ApiError(
      typeof body?.detail === "string"
        ? body.detail
        : `Не удалось выполнить запрос (${response.status}).`,
      response.status,
    );
  }
  if (!DEMO_MODE && response.headers.get("X-EduSpace-Demo") === "true") {
    throw new Error(
      "Сервер каталога работает в демо-режиме. Переключите DEMO_MODE=false на сервере.",
    );
  }
  return response.json() as Promise<T>;
}

export async function getTeachers(
  filters: CatalogFilters,
  signal?: AbortSignal,
  page = 1,
): Promise<TeacherPage> {
  if (DEMO_MODE) {
    const items: Teacher[] = demoTeachers.filter(
      (t) =>
        (!filters.subject || t.subjects.includes(filters.subject)) &&
        (!filters.language || t.languages.includes(filters.language)) &&
        t.price <= filters.maxPrice &&
        t.rating >= filters.rating &&
        (!filters.verified || t.is_verified),
    );
    items.sort((a, b) =>
      filters.sort === "price_asc"
        ? a.price - b.price
        : filters.sort === "price_desc"
          ? b.price - a.price
          : filters.sort === "reviews_desc"
            ? b.reviews_count - a.reviews_count
            : (b.rating ?? 0) - (a.rating ?? 0),
    );
    return {
      items: items.slice((page - 1) * 12, page * 12),
      total: items.length,
      page,
      page_size: 12,
      demo: true,
    };
  }
  const query = new URLSearchParams({
    subject: filters.subject,
    language: filters.language,
    max_price: String(filters.maxPrice),
    rating: String(filters.rating),
    verified: String(filters.verified),
    sort: filters.sort,
    page: String(page),
    page_size: "12",
  });
  return api<TeacherPage>(`/teachers?${query}`, { signal });
}

export async function getTeacher(
  id: string,
  signal?: AbortSignal,
): Promise<Teacher> {
  if (DEMO_MODE) {
    const teacher = demoTeachers.find((t) => String(t.id) === id);
    if (!teacher) throw new Error("Преподаватель не найден.");
    return teacher;
  }
  return api<Teacher>(`/teachers/${encodeURIComponent(id)}`, { signal });
}

export function authenticate(
  mode: "login" | "register",
  data: Record<string, string>,
) {
  return api<AuthResponse>(`/auth/${mode}`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}
