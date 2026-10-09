export type Role = "student" | "teacher";
export interface User {
  birth_date?: string | null;
  time_zone?: string | null;
  id: number;
  name: string;
  email: string;
  role: Role;
}
export interface Teacher {
  id: number;
  name: string;
  initials: string;
  subject: string;
  subjects: string[];
  languages: string[];
  bio: string;
  tagline: string;
  experience: number;
  price: number;
  rating: number | null;
  reviews_count: number;
  is_verified: boolean;
  color: string;
}
export interface TeacherPage {
  items: Teacher[];
  total: number;
  page: number;
  page_size: number;
  demo: boolean;
}
export interface CatalogFilters {
  subject: string;
  language: string;
  maxPrice: number;
  rating: number;
  verified: boolean;
  sort: string;
}
export interface Lesson {
  id: number;
  subject: string;
  topic: string;
  teacher: string;
  schedule: string;
  duration: number;
}
export interface LessonPage {
  items: Lesson[];
  total: number;
}
export interface AuthResponse {
  access_token: string;
  token_type: "bearer";
  user: User;
}
