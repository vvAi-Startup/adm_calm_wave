const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("calmwave_token");
}

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${endpoint}`, { ...options, headers });

  if (res.status === 401) {
    localStorage.removeItem("calmwave_token");
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Erro na requisição");
  return data as T;
}

/* Auth */
export const authAPI = {
  login: (email: string, password: string) =>
    fetchAPI<{ token: string; user: User }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  register: (name: string, email: string, password: string) =>
    fetchAPI<{ token: string; user: User }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password }),
    }),
  me: () => fetchAPI<{ user: User }>("/api/auth/me"),
};

/* Users */
export const usersAPI = {
  list: (params?: { page?: number; search?: string }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return fetchAPI<{ users: User[]; total: number; pages: number }>(
      `/api/users/?${q}`
    );
  },
  get: (id: number) => fetchAPI<{ user: User }>(`/api/users/${id}`),
  update: (id: number, data: Partial<User>) =>
    fetchAPI<{ user: User }>(`/api/users/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  delete: (id: number) =>
    fetchAPI<{ message: string }>(`/api/users/${id}`, { method: "DELETE" }),
  
  // Current user specifics
  updateSettings: (data: object) => fetchAPI<{ user: User }>(`/api/users/me/settings`, {
      method: "PUT",
      body: JSON.stringify(data),
  }),
  getDevices: () => fetchAPI<{ devices: Device[] }>(`/api/users/me/devices`),
  revokeDevice: (id: number) => fetchAPI<{ success: boolean }>(`/api/users/me/devices/${id}`, { method: "DELETE" }),
  revokeAllDevices: () => fetchAPI<{ success: boolean }>(`/api/users/me/devices/revoke_all`, { method: "POST" }),
  getAchievements: () => fetchAPI<{ achievements: Achievement[] }>(`/api/users/me/achievements`),
};

/* Audios */
export const audiosAPI = {
  list: (params?: { page?: number; processed?: string }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return fetchAPI<{ audios: Audio[]; total: number; pages: number }>(
      `/api/audios/?${q}`
    );
  },
  upload: async (file: File, deviceOrigin: string = "Web") => {
    const token = getToken();
    const formData = new FormData();
    formData.append("file", file);
    formData.append("device_origin", deviceOrigin);

    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${BASE_URL}/api/audios/upload`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (res.status === 401) {
      localStorage.removeItem("calmwave_token");
      window.location.href = "/login";
      throw new Error("Unauthorized");
    }

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Erro no upload");
    return data as { audio: Audio };
  },
  get: (id: number) => fetchAPI<{ audio: Audio }>(`/api/audios/${id}`),
  delete: (id: number) =>
    fetchAPI<{ message: string }>(`/api/audios/${id}`, { method: "DELETE" }),
  update: (id: number, data: object) =>
    fetchAPI<{ audio: Audio }>(`/api/audios/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
};

/* Stats */
export const statsAPI = {
  dashboard: () => fetchAPI<DashboardStats>("/api/stats/dashboard"),
  analytics: () => fetchAPI<AnalyticsData>("/api/stats/analytics"),
  status: () => fetchAPI<any>("/api/stats/status"),
};

/* Events */
export const eventsAPI = {
  list: (params?: { page?: number; level?: string }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return fetchAPI<{ events: Event[]; total: number }>(`/api/events/?${q}`);
  },
  create: (data: object) =>
    fetchAPI<{ event: Event }>("/api/events/", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

/* Types */
export interface User {
  id: number;
  email: string;
  name: string;
  profile_photo_url?: string;
  created_at: string;
  last_access: string;
  active: boolean;
  account_type: string;
  settings?: {
    dark_mode: boolean;
    notifications_enabled: boolean;
    auto_process_audio: boolean;
    audio_quality: string;
  }
}

export interface Device {
    id: number;
    device_name: string;
    device_type: string;
    ip_address: string;
    connected_at: string;
    last_active: string;
    is_current: boolean;
}

export interface Achievement {
    id: number;
    icon: string;
    name: string;
    desc: string;
    earned: boolean;
    count: number;
}

export interface Audio {
  id: number;
  user_id: number;
  filename: string;
  duration_seconds: number;
  size_bytes: number;
  recorded_at: string;
  processed: boolean;
  transcribed: boolean;
  transcription_text?: string;
  favorite: boolean;
  playlist_id?: number;
  device_origin?: string;
}

export interface DashboardStats {
  total_audios: number;
  total_users: number;
  processed_audios: number;
  processed_pct: number;
  recent_audios_week: number;
  streaming_sessions: number;
  system_status: string;
  daily_counts: { day: string; count: number }[];
  last_uploads: Audio[];
}

export interface AnalyticsData {
  total_active_users: number;
  total_users: number;
  session_duration: string;
  bounce_rate: number;
  total_audios: number;
  favorite_audios?: number;
  transcribed_audios?: number;
  user_growth: { month: string; users: number }[];
  features_usage: { name: string; usage: number }[];
  retention: { day: string; rate: number }[];
}

export interface Event {
  id: number;
  user_id?: number;
  event_type: string;
  created_at: string;
  details_json?: string;
  screen?: string;
  level: string;
}

export interface Notification {
  id: number;
  user_id?: number | null;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
}

export const notificationsAPI = {
  list: () => fetchAPI<Notification[]>("/api/notifications/"),
  markRead: (id: number) => fetchAPI<{message: string; notification: Notification}>(`/api/notifications/${id}/read`, { method: "PUT" }),
  markAllRead: () => fetchAPI<{message: string}>("/api/notifications/read-all", { method: "PUT" })
};
