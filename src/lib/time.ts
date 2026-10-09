export function zonedInput(value: string, timeZone: string): string {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(new Date(value));
  const get = (type: string) => parts.find((p) => p.type === type)!.value;
  return `${get("year")}-${get("month")}-${get("day")}T${get("hour")}:${get("minute")}`;
}
export function wallTimeToUtc(value: string, timeZone: string): string {
  const wall = Date.parse(value + ":00Z");
  if (!Number.isFinite(wall)) throw new Error("Проверьте дату и время.");
  // Obtain offsets on both sides of a possible daylight-saving transition.
  const candidates = new Set<number>();
  for (const delta of [-36, 0, 36]) {
    const sample = wall + delta * 3600000;
    const local = Date.parse(
      zonedInput(new Date(sample).toISOString(), timeZone) + ":00Z",
    );
    const candidate = wall - (local - sample);
    if (zonedInput(new Date(candidate).toISOString(), timeZone) === value)
      candidates.add(candidate);
  }
  if (candidates.size !== 1)
    throw new Error(
      "Это время пропущено или повторяется при переводе часов. Выберите другое время.",
    );
  return new Date([...candidates][0]).toISOString();
}
