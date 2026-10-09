import type { ReactNode } from "react";
import { Link, Navigate, Route, Routes, useParams } from "react-router-dom";
import Layout from "./components/layout/Layout";
import Home from "./pages/Home";
import Catalog from "./pages/Catalog";
import TeacherProfile from "./pages/TeacherProfile";
import StudentDashboard from "./pages/StudentDashboard";
import TeacherDashboard from "./pages/TeacherDashboard";
import LessonChat from "./pages/LessonChat";
import Login from "./pages/Login";
import Register from "./pages/Register";
import { DEMO_MODE } from "./lib/api";
import { useAuth } from "./lib/auth";
import Dialogs from "./pages/Dialogs";
import Library from "./pages/Library";
import Notifications from "./pages/Notifications";
import PasswordRecovery from "./pages/PasswordRecovery";
import Offers from "./pages/Offers";
import TutorPage from "./pages/TutorPage";
import Presentation from "./pages/Presentation";
import ProfileSettings from "./pages/ProfileSettings";
import LearningSection from "./pages/LearningSection";

function Protected({ children }: { children: ReactNode }) {
  const { user, ready } = useAuth();
  if (!ready) return <p className="container">Восстанавливаем вход…</p>;
  if (DEMO_MODE && !user) return children;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}
function LegacyLessonLink() {
  const { id } = useParams();
  return <Navigate to={`/lessons/${id}/chat`} replace />;
}
export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route
          path="settings"
          element={
            <Protected>
              <ProfileSettings />
            </Protected>
          }
        />
        <Route
          path=":mode/lessons"
          element={
            <Protected>
              <LearningSection />
            </Protected>
          }
        />
        <Route
          path=":mode/homework"
          element={
            <Protected>
              <LearningSection homework />
            </Protected>
          }
        />
        <Route path="presentation" element={<Presentation />} />
        <Route index element={<Home />} />
        <Route
          path="messages"
          element={
            <Protected>
              <Dialogs />
            </Protected>
          }
        />
        <Route
          path="library"
          element={
            <Protected>
              <Library />
            </Protected>
          }
        />
        <Route
          path="notifications"
          element={
            <Protected>
              <Notifications />
            </Protected>
          }
        />
        <Route path="offers" element={<Offers />} />
        <Route
          path="tutor"
          element={
            <Protected>
              <TutorPage />
            </Protected>
          }
        />
        <Route path="catalog" element={<Catalog />} />
        <Route path="teachers/:id" element={<TeacherProfile />} />
        <Route
          path="student"
          element={
            <Protected>
              <StudentDashboard />
            </Protected>
          }
        />
        <Route
          path="teacher"
          element={
            <Protected>
              <TeacherDashboard />
            </Protected>
          }
        />
        <Route
          path="lessons/:id/chat"
          element={
            <Protected>
              <LessonChat />
            </Protected>
          }
        />
        <Route path="lessons/:id/room" element={<LegacyLessonLink />} />
        <Route path="forgot-password" element={<PasswordRecovery />} />
        <Route path="reset-password" element={<PasswordRecovery reset />} />
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Register />} />
        <Route
          path="*"
          element={
            <div className="container empty-state">
              <span className="eyebrow">404</span>
              <h1>Здесь пока ничего нет</h1>
              <Link to="/" className="button">
                На главную
              </Link>
            </div>
          }
        />
      </Route>
    </Routes>
  );
}
