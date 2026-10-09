import { Link, useParams } from "react-router-dom";
import DashboardLayout from "../components/layout/DashboardLayout";
import LiveDashboard from "../components/layout/LiveDashboard";
import HomeworkPanel from "../components/lesson-card/HomeworkPanel";
import { useAuth } from "../lib/auth";
export default function LearningSection({
  homework = false,
}: {
  homework?: boolean;
}) {
  const { mode } = useParams();
  const teacher = mode === "teacher";
  const { user } = useAuth();
  return (
    <DashboardLayout teacher={teacher}>
      {!user ? (
        <p>
          <Link to="/login">Войдите</Link>, чтобы увидеть свои занятия и
          задания.
        </p>
      ) : homework ? (
        <>
          <h1>{teacher ? "Домашние работы учеников" : "Домашние задания"}</h1>
          <HomeworkPanel teacher={teacher} />
        </>
      ) : (
        <LiveDashboard teacher={teacher} section="lessons" />
      )}
    </DashboardLayout>
  );
}
