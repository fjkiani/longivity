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

// ── Test Orders ───────────────────────────────────────────────────────────────

export interface RecommendedPanel {
  panel_id: string;
  display_name: string;
  domain: string;
  ordering_tier: string;
  markers: string[];
  specimen_types: string[];
  fasting_required: boolean;
  turnaround_days: number | null;
  approximate_cost_usd: number;
  quest_panel_code: string | null;
  labcorp_panel_code: string | null;
  priority: "urgent" | "high" | "routine";
  reasons: string[];
}

export interface TestOrderSummary {
  total_panels_recommended: number;
  total_markers_to_collect: number;
  total_estimated_cost_usd: number;
  fasting_required: boolean;
  specimen_types_required: string[];
  tier1_coverage_pct: number;
  active_hallmarks: string[];
  escalation_rules_triggered: number;
}

export interface TestOrder {
  patient_id: string;
  generated_at: string;
  status: string;
  summary: TestOrderSummary;
  ordering_rationale: {
    gap_detection: {
      missing_tier1_count: number;
      missing_tier2_count: number;
      missing_tier3_count: number;
      missing_tier1_markers: string[];
      missing_panels: string[];
    };
    hallmark_driven: {
      active_hallmarks: string[];
      panels_from_hallmarks: string[];
    };
    escalation: {
      triggered_rules: Array<{
        rule_id: string;
        trigger_marker: string;
        trigger_value: number;
        condition: string;
        severity: string;
        recommended_panels: string[];
        rationale: string;
      }>;
      panels_from_escalation: string[];
    };
  };
  recommended_panels: RecommendedPanel[];
  requisition: {
    panels: Array<{
      panel_id: string;
      display_name: string;
      quest_code: string | null;
      labcorp_code: string | null;
      fasting_required: boolean;
      specimen_types: string[];
    }>;
    total_panels: number;
    total_estimated_cost_usd: number;
    fasting_required: boolean;
    specimen_requirements: string[];
  };
}

export interface SavedOrderSummary {
  order_id: string;
  status: string;
  generated_at: string;
  approved_at: string | null;
  summary: TestOrderSummary;
  notes: string | null;
}

export interface BiomarkerGaps {
  patient_id: string;
  tier1_coverage_pct: number;
  missing_tier1: Array<{ marker_key: string; display_name: string; domain: string; panel: string; clinical_significance: string }>;
  missing_tier2: Array<{ marker_key: string; display_name: string; domain: string; panel: string; clinical_significance: string }>;
  missing_tier3: Array<{ marker_key: string; display_name: string; domain: string; panel: string; clinical_significance: string }>;
  missing_panels_tier1: string[];
  existing_marker_count: number;
  total_tier1_markers: number;
}

export interface MarkerDetail {
  marker_key: string;
  display_name: string;
  aliases: string[];
  loinc_code: string | null;
  domain: string;
  panel: string;
  specimen: string;
  unit: string;
  clinical_low: number | null;
  clinical_high: number | null;
  longevity_optimal_low: number | null;
  longevity_optimal_high: number | null;
  sex_specific: boolean;
  ordering_tier: string;
  hallmarks: string[];
  escalation_triggers: Array<{ condition: string; order_markers: string[] }>;
  notes: string;
  clinical_significance: string;
}

export interface PanelDetail {
  panel_id: string;
  display_name: string;
  description: string;
  domain: string;
  markers: string[];
  specimen_types: string[];
  fasting_required: boolean;
  turnaround_days: number;
  approximate_cost_usd: number;
  quest_panel_code: string | null;
  labcorp_panel_code: string | null;
  ordering_tier: string;
  hallmarks_covered: string[];
  clinical_indication: string;
  longevity_relevance: string;
  marker_details?: MarkerDetail[];
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

// ── Test Orders API ───────────────────────────────────────────────────────────

export const testOrdersApi = {
  /** Run the 3-step agent and return recommendations (does NOT save). */
  generate: (patientId: string) =>
    request<TestOrder>(`/api/v1/patients/${patientId}/test-order`),

  /** Approve and save an order to the database. */
  approve: (patientId: string, notes?: string, panelIdsToInclude?: string[]) =>
    request<SavedOrderSummary>(`/api/v1/patients/${patientId}/test-order`, {
      method: "POST",
      body: JSON.stringify({
        notes: notes || null,
        panel_ids_to_include: panelIdsToInclude || null,
      }),
    }),

  /** List all saved orders for a patient. */
  list: (patientId: string) =>
    request<SavedOrderSummary[]>(`/api/v1/patients/${patientId}/test-orders`),

  /** Get a specific saved order. */
  get: (patientId: string, orderId: string) =>
    request<TestOrder & { order_id: string }>(`/api/v1/patients/${patientId}/test-order/${orderId}`),

  /** Get the requisition for a saved order. */
  getRequisition: (patientId: string, orderId: string) =>
    request<any>(`/api/v1/patients/${patientId}/test-order/${orderId}/requisition`),

  /** Get biomarker gaps for a patient (Step A only). */
  getGaps: (patientId: string) =>
    request<BiomarkerGaps>(`/api/v1/patients/${patientId}/biomarker-gaps`),
};


// ─── Intelligence Types ───────────────────────────────────────────────────────

export interface ScoredAction {
  type: string;
  score: number;
  label: string;
  reason: string;
  urgency: "high" | "medium" | "low" | "routine";
  cta_url?: string;
  cta_label?: string;
}

export interface BiologicalSummary {
  phenoage_estimate: number | null;
  chronological_age: number | null;
  age_acceleration: number | null;
  accel_tier: string | null;
  hallmarks_activated: string[];
  top_accelerator: string | null;
  data_completeness_pct: number;
}

export interface GapSummaryIntel {
  tier1_coverage_pct: number;
  missing_tier1_count: number;
  missing_panels: string[];
  escalation_rules_firing: number;
}

export interface TopCompound {
  compound_id: string;
  display_name: string;
  relevance_score: number;
  hallmark: string;
  evidence_tier: string;
}

export interface TimelineSummary {
  first_panel_date: string | null;
  latest_panel_date: string | null;
  panel_count: number;
  last_assessment_date: string | null;
  last_order_date: string | null;
  days_since_last_action: number | null;
}

export interface ScoringBreakdown {
  data_urgency: number;
  phenoage_urgency: number;
  escalation_severity: number;
  time_decay: number;
  hallmark_signal: number;
  weights: Record<string, number>;
}

export interface IntelligenceResponse {
  patient_id: string;
  computed_at: string;
  cache_hit: boolean;
  current_state: string;
  current_state_label: string;
  current_state_color: string;
  urgency_score: number;
  next_action: ScoredAction | null;
  available_actions: ScoredAction[];
  biological_summary: BiologicalSummary;
  gap_summary: GapSummaryIntel;
  top_compound: TopCompound | null;
  timeline_summary: TimelineSummary;
  scoring_breakdown: ScoringBreakdown;
}

export interface TimelineEvent {
  id: string;
  event_type: string;
  event_at: string;
  source: string;
  actor_name: string | null;
  summary: string;
  payload: Record<string, unknown>;
}

export interface PatientTimeline {
  patient_id: string;
  events: TimelineEvent[];
}

// ─── Intelligence API ─────────────────────────────────────────────────────────

export const intelligenceApi = {
  getPatientIntelligence: async (
    patientId: string,
    forceRefresh = false
  ): Promise<IntelligenceResponse> => {
    const token = getToken();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const url = `${BASE}/api/v1/patients/${patientId}/intelligence${forceRefresh ? "?force_refresh=true" : ""}`;
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`Intelligence fetch failed: ${res.status}`);
    return res.json();
  },

  getClinicIntelligence: async (params?: {
    state?: string;
    min_urgency?: number;
    limit?: number;
    offset?: number;
  }): Promise<IntelligenceResponse[]> => {
    const token = getToken();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const qs = new URLSearchParams();
    if (params?.state) qs.set("state", params.state);
    if (params?.min_urgency != null) qs.set("min_urgency", String(params.min_urgency));
    if (params?.limit != null) qs.set("limit", String(params.limit));
    if (params?.offset != null) qs.set("offset", String(params.offset));
    const url = `${BASE}/api/v1/clinic/intelligence${qs.toString() ? "?" + qs.toString() : ""}`;
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`Clinic intelligence fetch failed: ${res.status}`);
    return res.json();
  },

  getPatientTimeline: async (patientId: string): Promise<PatientTimeline> => {
    const token = getToken();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${BASE}/api/v1/patients/${patientId}/timeline`, { headers });
    if (!res.ok) throw new Error(`Timeline fetch failed: ${res.status}`);
    return res.json();
  },
};

// ── Registry API ──────────────────────────────────────────────────────────────

export const registryApi = {
  /** List all markers with optional filtering. */
  listMarkers: (params?: { domain?: string; tier?: string; search?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.domain) qs.set("domain", params.domain);
    if (params?.tier) qs.set("tier", params.tier);
    if (params?.search) qs.set("search", params.search);
    if (params?.limit) qs.set("limit", String(params.limit));
    return request<{ total: number; markers: MarkerDetail[] }>(`/api/v1/markers?${qs}`);
  },

  /** Get a single marker by key. */
  getMarker: (markerKey: string) =>
    request<MarkerDetail>(`/api/v1/markers/${markerKey}`),

  /** List all orderable panels. */
  listPanels: (params?: { tier?: string; domain?: string; search?: string }) => {
    const qs = new URLSearchParams();
    if (params?.tier) qs.set("tier", params.tier);
    if (params?.domain) qs.set("domain", params.domain);
    if (params?.search) qs.set("search", params.search);
    return request<{ total: number; panels: PanelDetail[] }>(`/api/v1/panels?${qs}`);
  },

  /** Get a single panel by ID. */
  getPanel: (panelId: string) =>
    request<PanelDetail>(`/api/v1/panels/${panelId}`),

  /** Get registry metadata. */
  getMetadata: () => request<any>("/api/v1/registry/metadata"),
};

// ── Demo API ──────────────────────────────────────────────────────────────────

export interface DemoPatientSummary {
  mrn: string;
  name: string;
  age: number | null;
  sex: string | null;
  condition: string;
}

export interface DemoStatus {
  seeded: boolean;
  message?: string;
  seeded_at?: string | null;
  credentials?: {
    email: string;
    password: string;
    note: string;
  } | null;
  clinic?: string;
  patient_count?: number;
  patients?: DemoPatientSummary[];
  data_sources?: string[];
}

export const demoApi = {
  getStatus: async (): Promise<DemoStatus> => {
    const res = await fetch(`${BASE}/api/v1/demo/status`);
    if (!res.ok) throw new Error(`Demo status failed: ${res.status}`);
    return res.json();
  },
};

// ── Evidence API ──────────────────────────────────────────────────────────────

export interface EvidencePaper {
  pmid?: string;
  title?: string;
  year?: number;
  study_type?: string;
  journal?: string;
}

export interface CompoundEvidence {
  compound: string;
  hallmark: string;
  evidence_tier: string;
  summary: string;
  papers: EvidencePaper[];
  confidence: number;
  cached: boolean;
  fallback?: boolean;
}

export interface HallmarkNarrative {
  hallmark: string;
  headline: string;
  narrative: string;
  key_biomarkers: string[];
  citations: string[];
  evidence_tier: string;
  cached: boolean;
}

export interface CancerRiskSummary {
  overall_risk_tier: "HIGH" | "MODERATE" | "LOW" | "UNKNOWN";
  genomic_instability_score: number | null;
  inflammatory_burden_score: number | null;
  synthesis: string;
  recommended_surveillance: string[];
  citations: string[];
  evidence_tier: string;
  message?: string;
}

function authHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("longivity_token") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const evidenceApi = {
  getCompoundEvidence: async (
    patientId: string,
    compoundId: string,
    hallmark = "longevity"
  ): Promise<CompoundEvidence> => {
    const res = await fetch(
      `${BASE}/api/v1/patients/${patientId}/evidence/compound/${compoundId}?hallmark=${hallmark}`,
      { headers: authHeaders() }
    );
    if (!res.ok) throw new Error(`Evidence fetch failed: ${res.status}`);
    return res.json();
  },

  getHallmarkNarrative: async (
    patientId: string,
    hallmark: string
  ): Promise<HallmarkNarrative> => {
    const res = await fetch(
      `${BASE}/api/v1/patients/${patientId}/evidence/hallmark/${hallmark}`,
      { headers: authHeaders() }
    );
    if (!res.ok) throw new Error(`Hallmark evidence failed: ${res.status}`);
    return res.json();
  },

  getCancerRisk: async (patientId: string): Promise<CancerRiskSummary> => {
    const res = await fetch(
      `${BASE}/api/v1/patients/${patientId}/evidence/cancer-risk`,
      { headers: authHeaders() }
    );
    if (!res.ok) throw new Error(`Cancer risk fetch failed: ${res.status}`);
    return res.json();
  },

  research: async (query: string, context?: Record<string, unknown>) => {
    const res = await fetch(`${BASE}/api/v1/research-intelligence/research`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ query, context }),
    });
    if (!res.ok) throw new Error(`Research failed: ${res.status}`);
    return res.json();
  },
};
