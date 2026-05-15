/**
 * API client — typed wrappers around the Longivity FastAPI backend.
 */

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  clinic_id: string;
  email: string;
  full_name: string | null;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string | null;
  clinic_id: string;
  role: string;
}

// ── Patients ──────────────────────────────────────────────────────────────────

export interface Patient {
  id: string;
  clinic_id: string;
  first_name: string;
  last_name: string;
  date_of_birth: string | null;
  sex: string | null;
  mrn: string | null;
  email: string | null;
  phone: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  panel_count: number;
  latest_panel_date: string | null;
  age: number | null;
}

export interface PatientCreate {
  first_name: string;
  last_name: string;
  date_of_birth?: string;
  sex?: string;
  mrn?: string;
  email?: string;
  phone?: string;
  notes?: string;
}

// ── Panels ────────────────────────────────────────────────────────────────────

export interface PanelValue {
  marker_key: string;
  marker_display: string | null;
  value: number;
  unit: string | null;
  ref_low: number | null;
  ref_high: number | null;
  flag: string | null;
}

export interface Panel {
  id: string;
  patient_id: string;
  drawn_at: string;
  source: string;
  lab_name: string | null;
  notes: string | null;
  created_at: string;
  values: PanelValue[];
}

// ── Assessment ────────────────────────────────────────────────────────────────

export interface Assessment {
  phenoage_result?: {
    phenoage_estimate: number | null;
    phenoage_acceleration: number | null;
    accel_tier: string;
    accel_tier_label: string;
    components_used: number;
    missing_components: string[];
  };
  hallmark_result?: {
    hallmarks_activated: string[];
    hallmark_scores: Record<string, number>;
    narrative: string;
  };
  compound_recommendations?: Array<{
    compound_id: string;
    display_name: string;
    relevance_score: number;
    evidence_tier: string;
    evidence_tier_label: string;
    mr_anchor: string | null;
    hallmarks_targeted: string[];
  }>;
  _meta?: {
    patient_id: string;
    panel_id: string;
    drawn_at: string;
    source: string;
    lab_name: string | null;
  };
}

// ── HTTP helpers ──────────────────────────────────────────────────────────────

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("longivity_token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Auth API ──────────────────────────────────────────────────────────────────

export const authApi = {
  register: (email: string, password: string, fullName: string, clinicName: string) =>
    request<TokenResponse>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName, clinic_name: clinicName }),
    }),

  login: (email: string, password: string) =>
    request<TokenResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<UserResponse>("/api/v1/auth/me"),
};

// ── Patients API ──────────────────────────────────────────────────────────────

export const patientsApi = {
  list: () => request<Patient[]>("/api/v1/patients"),

  get: (id: string) => request<Patient>(`/api/v1/patients/${id}`),

  create: (data: PatientCreate) =>
    request<Patient>("/api/v1/patients", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<PatientCreate>) =>
    request<Patient>(`/api/v1/patients/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    request<void>(`/api/v1/patients/${id}`, { method: "DELETE" }),
};

// ── Panels API ────────────────────────────────────────────────────────────────

export const panelsApi = {
  list: (patientId: string) =>
    request<Panel[]>(`/api/v1/patients/${patientId}/panels`),

  get: (patientId: string, panelId: string) =>
    request<Panel>(`/api/v1/patients/${patientId}/panels/${panelId}`),

  create: (patientId: string, data: {
    drawn_at: string;
    source?: string;
    lab_name?: string;
    notes?: string;
    values: PanelValue[];
  }) =>
    request<Panel>(`/api/v1/patients/${patientId}/panels`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  uploadPdf: async (patientId: string, file: File, drawnAt?: string) => {
    const token = getToken();
    const formData = new FormData();
    formData.append("file", file);
    if (drawnAt) formData.append("drawn_at", drawnAt);

    const res = await fetch(`${BASE}/api/v1/patients/${patientId}/upload`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },
};

// ── Assessment API ────────────────────────────────────────────────────────────

export const assessmentApi = {
  getAssessment: (patientId: string, compoundQueries?: string) =>
    request<Assessment>(
      `/api/v1/patients/${patientId}/assessment${compoundQueries ? `?compound_queries=${compoundQueries}` : ""}`
    ),

  getLongitudinal: (patientId: string) =>
    request<any>(`/api/v1/patients/${patientId}/longitudinal`),

  getNof1: (patientId: string, compoundId: string) =>
    request<any>(`/api/v1/patients/${patientId}/nof1/${compoundId}`),
};
