import { useTimeZone } from "../../lib/useTimeZone";
import { useEffect, useState, type FormEvent } from "react";
import { UploadFile } from "../UploadFile";
import ServiceManager, { type Service } from "./ServiceManager";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import type { Teacher, User } from "../../types";
type Slot = {
  id: number;
  start_time: string;
  duration_min: number;
  is_booked: boolean;
  service_id?: number;
  service_title?: string;
  price?: number;
};
export default function TeacherServices() {
  const { timeZone, formatDate, toInput, fromInput } = useTimeZone();
  const { token, updateUser } = useAuth();
  const [services, setServices] = useState<Service[]>([]);
  const [editingSlot, setEditingSlot] = useState<Slot>();
  const [offer, setOffer] = useState<Teacher | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  async function load() {
    try {
      const item = await api<Teacher | null>("/offers/mine", {}, token);
      setOffer(item);
      if (item) {
        setSlots(await api<Slot[]>("/offers/mine/slots", {}, token));
        setServices(await api<Service[]>("/offers/mine/services", {}, token));
      }
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setLoaded(true);
    }
  }
  useEffect(() => {
    void load();
  }, [token]);
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setMessage("");
    try {
      await api(
        "/offers/mine",
        {
          method: "POST",
          body: JSON.stringify({
            subject: form.get("subject"),
            languages: String(form.get("languages"))
              .split(",")
              .map((s) => s.trim())
              .filter(Boolean),
            bio: form.get("bio"),
            price: form.get("price"),
            experience: Number(form.get("experience")),
          }),
        },
        token,
      );
      await load();
      updateUser(await api<User>("/auth/me", {}, token));
      setMessage(
        "Профиль опубликован. Добавьте свободные даты, чтобы ученики могли записаться.",
      );
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Ошибка сохранения");
    } finally {
      setBusy(false);
    }
  }
  async function add(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setMessage("");
    try {
      await api(
        "/offers/mine/slots" + (editingSlot ? `/${editingSlot.id}` : ""),
        {
          method: editingSlot ? "PATCH" : "POST",
          body: JSON.stringify({
            service_id: form.get("service")
              ? Number(form.get("service"))
              : null,
            start_time: fromInput(String(form.get("start"))),
            duration_min: Number(form.get("duration")),
          }),
        },
        token,
      );
      await load();
      setEditingSlot(undefined);
      setMessage("Время сохранено.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Ошибка добавления");
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel spaced">
      <h2>{offer ? "Моя услуга и расписание" : "Стать преподавателем"}</h2>
      <p>
        Заполните профиль, затем добавьте свободное время. Вы сможете
        одновременно преподавать и учиться. Публикация бесплатна.
      </p>
      {message && (
        <p role="status" className="notice">
          {message}
        </p>
      )}
      {loaded && (
        <form
          key={offer?.id ?? "new"}
          onSubmit={save}
          className="learning-form"
        >
          <label>
            Предмет или услуга
            <input
              name="subject"
              required
              minLength={2}
              maxLength={100}
              defaultValue={offer?.subject}
            />
          </label>
          <label>
            Языки обучения через запятую
            <input
              name="languages"
              required
              defaultValue={offer?.languages.join(", ") ?? "Русский"}
            />
          </label>
          <label>
            О себе и занятиях
            <textarea
              name="bio"
              required
              minLength={10}
              maxLength={5000}
              defaultValue={offer?.bio}
            />
          </label>
          <label>
            Цена одного занятия, сом
            <input
              name="price"
              type="number"
              min="0"
              max="100000"
              step="0.01"
              required
              defaultValue={offer?.price ?? 600}
            />
          </label>
          <label>
            Опыт, лет
            <input
              name="experience"
              type="number"
              min="0"
              max="80"
              defaultValue={offer?.experience ?? 0}
            />
          </label>
          <button className="button" disabled={busy}>
            {offer ? "Сохранить услугу" : "Опубликовать услугу"}
          </button>
        </form>
      )}
      {offer && (
        <>
          <UploadFile path="/files/avatar" photo />
          <ServiceManager onChange={() => void load()} />
          <h3>{editingSlot ? "Изменить время" : "Добавить свободное время"}</h3>
          <p>Часовой пояс: {timeZone}. Выберите услугу для этого времени.</p>
          <form
            key={editingSlot?.id ?? "new-slot"}
            onSubmit={add}
            className="learning-form"
          >
            <label>
              Услуга
              <select
                name="service"
                defaultValue={editingSlot?.service_id ?? ""}
              >
                <option value="">Основная услуга профиля</option>
                {services.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.title} — {s.price} сом
                  </option>
                ))}
              </select>
            </label>
            <label>
              Дата и время
              <input
                name="start"
                type="datetime-local"
                required
                defaultValue={
                  editingSlot ? toInput(editingSlot.start_time) : ""
                }
              />
            </label>
            <label>
              Длительность, минут
              <select
                name="duration"
                defaultValue={editingSlot?.duration_min ?? 30}
              >
                <option>30</option>
                <option>45</option>
                <option>60</option>
              </select>
            </label>
            <button className="button" disabled={busy}>
              Сохранить время
            </button>
          </form>
          {slots.map((slot) => (
            <p key={slot.id}>
              {formatDate(slot.start_time)} · {slot.duration_min} мин ·{" "}
              {slot.is_booked ? "Забронировано" : "Свободно"} ·{" "}
              {slot.service_title} · {slot.price} сом
              {!slot.is_booked && (
                <>
                  <button type="button" onClick={() => setEditingSlot(slot)}>
                    Изменить
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={async () => {
                      if (!confirm("Удалить свободное время?")) return;
                      setBusy(true);
                      try {
                        await api(
                          `/offers/mine/slots/${slot.id}`,
                          { method: "DELETE" },
                          token,
                        );
                        await load();
                      } catch (e) {
                        setMessage(String(e));
                      } finally {
                        setBusy(false);
                      }
                    }}
                  >
                    Удалить
                  </button>
                </>
              )}
            </p>
          ))}
        </>
      )}
    </section>
  );
}
