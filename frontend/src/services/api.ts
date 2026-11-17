/**
 * AgriConnect Typed API Client
 */

const API_BASE = "http://localhost:8000/api/v1";

export interface CropStage {
  stage_id: string;
  label_en: string;
  label_kn: string;
}

export interface CatalogCrop {
  crop_id: string;
  name_en: string;
  name_kn: string;
  typical_duration_days: number;
  stages: CropStage[];
}

export interface FarmerProfile {
  id: number;
  phone_number: string;
  full_name: string;
  preferred_lang: string;
  dpdp_consent: boolean;
  dpdp_consent_time: string;
  dpdp_consent_withdrawn_time: string | null;
  dpdp_policy_version: string;
  image_training_consent: boolean;
  image_training_consent_time: string | null;
  has_farms: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
  farmer: FarmerProfile;
}

export interface CropRecord {
  crop_record_id: number;
  farm_id: number;
  crop_id: string;
  sowing_date: string;
  current_stage: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface FarmRecord {
  id: number;
  farmer_id: number;
  name: string;
  latitude: number;
  longitude: number;
  area_acres: number;
  water_source: string;
  water_availability: string;
  irrigation_type: string;
  pump_discharge_rate: number | null;
  pump_rate_provenance: string | null;
  soil_type: string;
  created_at: string;
  updated_at: string;
  crops: CropRecord[];
}

export interface FarmCreatePayload {
  name: string;
  latitude: number;
  longitude: number;
  area_acres: number;
  water_source: string;
  water_availability: string;
  irrigation_type: string;
  pump_discharge_rate?: number | null;
  pump_rate_provenance?: string | null;
  soil_type: string;
}

export interface CropCreatePayload {
  crop_id: string;
  sowing_date: string;
  current_stage: string;
}

export function getAuthToken(): string | null {
  return localStorage.getItem("agriconnect_token");
}

export function setAuthToken(token: string): void {
  localStorage.setItem("agriconnect_token", token);
}

export function clearAuthToken(): void {
  localStorage.removeItem("agriconnect_token");
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const data = await res.json();
      if (data.detail) {
        errorDetail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // Keep default error
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export const api = {
  // Auth
  devLogin: (payload: {
    phone_number: string;
    otp: string;
    full_name?: string;
    preferred_lang?: string;
    dpdp_consent: boolean;
    image_training_consent?: boolean;
  }) => request<TokenResponse>("/auth/dev-login", {
    method: "POST",
    body: JSON.stringify(payload),
  }),

  getMe: () => request<FarmerProfile>("/auth/me"),

  updateConsent: (payload: {
    dpdp_consent?: boolean;
    image_training_consent?: boolean;
  }) => request<FarmerProfile>("/auth/consent", {
    method: "PATCH",
    body: JSON.stringify(payload),
  }),

  // Crops Catalog
  getCropsCatalog: () => request<CatalogCrop[]>("/crops/catalog"),

  // Farms
  createFarm: (payload: FarmCreatePayload) => request<FarmRecord>("/farms", {
    method: "POST",
    body: JSON.stringify(payload),
  }),

  listFarms: () => request<FarmRecord[]>("/farms"),

  getFarm: (farmId: number) => request<FarmRecord>(`/farms/${farmId}`),

  updateFarm: (farmId: number, payload: Partial<FarmCreatePayload>) => request<FarmRecord>(`/farms/${farmId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  }),

  deleteFarm: (farmId: number) => request<{ status: string; message: string }>(`/farms/${farmId}`, {
    method: "DELETE",
  }),

  // Crops on Farm
  registerCrop: (farmId: number, payload: CropCreatePayload) => request<CropRecord>(`/farms/${farmId}/crops`, {
    method: "POST",
    body: JSON.stringify(payload),
  }),

  listCrops: (farmId: number) => request<CropRecord[]>(`/farms/${farmId}/crops`),

  updateCrop: (farmId: number, cropRecordId: number, payload: { sowing_date?: string; current_stage?: string }) =>
    request<CropRecord>(`/farms/${farmId}/crops/${cropRecordId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  deactivateCrop: (farmId: number, cropRecordId: number) =>
    request<CropRecord>(`/farms/${farmId}/crops/${cropRecordId}/deactivate`, {
      method: "PATCH",
    }),

  // Privacy
  exportData: () => request<any>("/privacy/export"),

  deleteAccount: () => request<{ status: string; message: string }>("/privacy/delete-account", {
    method: "DELETE",
  }),
};
