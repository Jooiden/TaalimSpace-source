import { useAuth } from "./auth";
import { wallTimeToUtc, zonedInput } from "./time";
export function useTimeZone() {
  const { user } = useAuth();
  const timeZone =
    user?.time_zone ||
    Intl.DateTimeFormat().resolvedOptions().timeZone ||
    "UTC";
  return {
    timeZone,
    formatDate: (value: string, options?: Intl.DateTimeFormatOptions) =>
      new Intl.DateTimeFormat("ru-RU", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        ...options,
        timeZone,
      }).format(new Date(value)),
    dateKey: (value: string) => zonedInput(value, timeZone).slice(0, 10),
    toInput: (value: string) => zonedInput(value, timeZone),
    fromInput: (value: string) => wallTimeToUtc(value, timeZone),
  };
}
