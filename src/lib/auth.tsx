import {
  createContext,
  useContext,
  useState,
  useEffect,
  useRef,
  type ReactNode,
} from "react";
import { api, ApiError } from "./api";
import type { AuthResponse, User } from "../types";

interface AuthContextValue {
  ready: boolean;
  user: User | null;
  token: string | undefined;
  signIn: (data: AuthResponse) => void;
  signOut: () => void;
  updateUser: (user: User) => void;
}
const AuthContext = createContext<AuthContextValue | null>(null);
export function AuthProvider({ children }: { children: ReactNode }) {
  const version = useRef(0);
  const [ready, setReady] = useState(false);
  const [session, setSession] = useState<AuthResponse | null>(null);
  const [refreshError, setRefreshError] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    const refresh = () => {
      const started = version.current;
      return api<AuthResponse>("/auth/refresh", { method: "POST" })
        .then((data) => {
          if (active && started === version.current) {
            setSession(data);
            setRefreshError(false);
          }
        })
        .catch((error: unknown) => {
          if (!active || started !== version.current) return;
          if (error instanceof ApiError && error.status === 401) {
            setSession(null);
            setRefreshError(false);
          } else {
            setRefreshError(true);
          }
        })
        .finally(() => {
          if (active) setReady(true);
        });
    };
    void refresh();
    const timer = setInterval(refresh, 10 * 60 * 1000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [retry]);
  return (
    <AuthContext.Provider
      value={{
        ready,
        user: session?.user ?? null,
        token: session?.access_token,
        signIn: (data) => {
          version.current++;
          setSession(data);
          setRefreshError(false);
        },
        updateUser: (user) =>
          setSession((current) => (current ? { ...current, user } : null)),
        signOut: () => {
          void api("/auth/logout", { method: "POST" })
            .then(() => {
              version.current++;
              setSession(null);
              setRefreshError(false);
            })
            .catch(() =>
              alert("Не удалось выйти. Проверьте соединение и повторите."),
            );
        },
      }}
    >
      {refreshError && (
        <div
          role="alert"
          className="bg-amber-50 px-4 py-3 text-center text-sm text-amber-950"
        >
          Не удалось проверить вход. Проверьте соединение с сервером.
          <button
            type="button"
            className="ml-3 font-semibold underline"
            onClick={() => setRetry((value) => value + 1)}
          >
            Повторить
          </button>
        </div>
      )}
      {children}
    </AuthContext.Provider>
  );
}
export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("AuthProvider is required");
  return value;
}
