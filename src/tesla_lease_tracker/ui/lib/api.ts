import { useQuery, useSuspenseQuery, useMutation } from "@tanstack/react-query";
import type { UseQueryOptions, UseSuspenseQueryOptions, UseMutationOptions } from "@tanstack/react-query";

export interface ComplexValue {
  display?: string | null;
  primary?: boolean | null;
  ref?: string | null;
  type?: string | null;
  value?: string | null;
}

export interface DashboardOut {
  budget_daily_rate: number;
  daily_average: number;
  days_remaining: number;
  last_odometer?: number | null;
  last_sync?: string | null;
  lease_miles_used: number;
  mileage_limit: number;
  over_under: number;
  projected_end_miles: number;
  total_lease_days: number;
}

export interface ForecastOut {
  daily_rate: number;
  model: string;
  over_under: number;
  points: ForecastPoint[];
  projected_end_miles: number;
}

export interface ForecastPoint {
  date: string;
  lower_bound?: number | null;
  predicted_miles: number;
  upper_bound?: number | null;
}

export interface HTTPValidationError {
  detail?: ValidationError[];
}

export interface HealthOut {
  has_lease: boolean;
  last_sync?: string | null;
  readings_count: number;
  status: string;
  version: string;
}

export interface LeaseConfigIn {
  lease_end_date: string;
  lease_start_date: string;
  mileage_limit: number;
  start_odometer: number;
  vin: string;
}

export interface LeaseConfigOut {
  created_at: string;
  lease_end_date: string;
  lease_start_date: string;
  mileage_limit: number;
  start_odometer: number;
  updated_at: string;
  vin: string;
}

export interface MileageReadingOut {
  lease_miles: number;
  odometer: number;
  timestamp: string;
}

export interface Name {
  family_name?: string | null;
  given_name?: string | null;
}

export interface User {
  active?: boolean | null;
  display_name?: string | null;
  emails?: ComplexValue[] | null;
  entitlements?: ComplexValue[] | null;
  external_id?: string | null;
  groups?: ComplexValue[] | null;
  id?: string | null;
  name?: Name | null;
  roles?: ComplexValue[] | null;
  schemas?: UserSchema[] | null;
  user_name?: string | null;
}

export const UserSchema = {
  "urn:ietf:params:scim:schemas:core:2.0:User": "urn:ietf:params:scim:schemas:core:2.0:User",
  "urn:ietf:params:scim:schemas:extension:workspace:2.0:User": "urn:ietf:params:scim:schemas:extension:workspace:2.0:User",
} as const;

export type UserSchema = (typeof UserSchema)[keyof typeof UserSchema];

export interface ValidationError {
  ctx?: Record<string, unknown>;
  input?: unknown;
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface VersionOut {
  version: string;
}

export interface CurrentUserParams {
  "X-Forwarded-Access-Token"?: string | null;
}

export interface GetForecastParams {
  model?: string;
}

export class ApiError extends Error {
  status: number;
  statusText: string;
  body: unknown;

  constructor(status: number, statusText: string, body: unknown) {
    super(`HTTP ${status}: ${statusText}`);
    this.name = "ApiError";
    this.status = status;
    this.statusText = statusText;
    this.body = body;
  }
}

export const currentUser = async (params?: CurrentUserParams, options?: RequestInit): Promise<{ data: User }> => {
  const res = await fetch("/api/current-user", { ...options, method: "GET", headers: { ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers } });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const currentUserKey = (params?: CurrentUserParams) => {
  return ["/api/current-user", params] as const;
};

export function useCurrentUser<TData = { data: User }>(options?: { params?: CurrentUserParams; query?: Omit<UseQueryOptions<{ data: User }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: currentUserKey(options?.params), queryFn: () => currentUser(options?.params), ...options?.query });
}

export function useCurrentUserSuspense<TData = { data: User }>(options?: { params?: CurrentUserParams; query?: Omit<UseSuspenseQueryOptions<{ data: User }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: currentUserKey(options?.params), queryFn: () => currentUser(options?.params), ...options?.query });
}

export const getDashboard = async (options?: RequestInit): Promise<{ data: DashboardOut | null }> => {
  const res = await fetch("/api/dashboard", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const getDashboardKey = () => {
  return ["/api/dashboard"] as const;
};

export function useGetDashboard<TData = { data: DashboardOut | null }>(options?: { query?: Omit<UseQueryOptions<{ data: DashboardOut | null }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: getDashboardKey(), queryFn: () => getDashboard(), ...options?.query });
}

export function useGetDashboardSuspense<TData = { data: DashboardOut | null }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: DashboardOut | null }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: getDashboardKey(), queryFn: () => getDashboard(), ...options?.query });
}

export const getForecast = async (params?: GetForecastParams, options?: RequestInit): Promise<{ data: ForecastOut }> => {
  const searchParams = new URLSearchParams();
  if (params?.model != null) searchParams.set("model", String(params?.model));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/forecast?${queryString}` : `/api/forecast`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const getForecastKey = (params?: GetForecastParams) => {
  return ["/api/forecast", params] as const;
};

export function useGetForecast<TData = { data: ForecastOut }>(options?: { params?: GetForecastParams; query?: Omit<UseQueryOptions<{ data: ForecastOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: getForecastKey(options?.params), queryFn: () => getForecast(options?.params), ...options?.query });
}

export function useGetForecastSuspense<TData = { data: ForecastOut }>(options?: { params?: GetForecastParams; query?: Omit<UseSuspenseQueryOptions<{ data: ForecastOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: getForecastKey(options?.params), queryFn: () => getForecast(options?.params), ...options?.query });
}

export const getHealth = async (options?: RequestInit): Promise<{ data: HealthOut }> => {
  const res = await fetch("/api/health", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const getHealthKey = () => {
  return ["/api/health"] as const;
};

export function useGetHealth<TData = { data: HealthOut }>(options?: { query?: Omit<UseQueryOptions<{ data: HealthOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: getHealthKey(), queryFn: () => getHealth(), ...options?.query });
}

export function useGetHealthSuspense<TData = { data: HealthOut }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: HealthOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: getHealthKey(), queryFn: () => getHealth(), ...options?.query });
}

export const getLease = async (options?: RequestInit): Promise<{ data: LeaseConfigOut | null }> => {
  const res = await fetch("/api/lease", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const getLeaseKey = () => {
  return ["/api/lease"] as const;
};

export function useGetLease<TData = { data: LeaseConfigOut | null }>(options?: { query?: Omit<UseQueryOptions<{ data: LeaseConfigOut | null }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: getLeaseKey(), queryFn: () => getLease(), ...options?.query });
}

export function useGetLeaseSuspense<TData = { data: LeaseConfigOut | null }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: LeaseConfigOut | null }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: getLeaseKey(), queryFn: () => getLease(), ...options?.query });
}

export const saveLease = async (data: LeaseConfigIn, options?: RequestInit): Promise<{ data: LeaseConfigOut }> => {
  const res = await fetch("/api/lease", { ...options, method: "PUT", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useSaveLease(options?: { mutation?: UseMutationOptions<{ data: LeaseConfigOut }, ApiError, LeaseConfigIn> }) {
  return useMutation({ mutationFn: (data) => saveLease(data), ...options?.mutation });
}

export const getMileage = async (options?: RequestInit): Promise<{ data: MileageReadingOut[] }> => {
  const res = await fetch("/api/mileage", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const getMileageKey = () => {
  return ["/api/mileage"] as const;
};

export function useGetMileage<TData = { data: MileageReadingOut[] }>(options?: { query?: Omit<UseQueryOptions<{ data: MileageReadingOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: getMileageKey(), queryFn: () => getMileage(), ...options?.query });
}

export function useGetMileageSuspense<TData = { data: MileageReadingOut[] }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: MileageReadingOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: getMileageKey(), queryFn: () => getMileage(), ...options?.query });
}

export const syncMileage = async (options?: RequestInit): Promise<{ data: MileageReadingOut }> => {
  const res = await fetch("/api/mileage/sync", { ...options, method: "POST" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useSyncMileage(options?: { mutation?: UseMutationOptions<{ data: MileageReadingOut }, ApiError, void> }) {
  return useMutation({ mutationFn: () => syncMileage(), ...options?.mutation });
}

export const version = async (options?: RequestInit): Promise<{ data: VersionOut }> => {
  const res = await fetch("/api/version", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const versionKey = () => {
  return ["/api/version"] as const;
};

export function useVersion<TData = { data: VersionOut }>(options?: { query?: Omit<UseQueryOptions<{ data: VersionOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: versionKey(), queryFn: () => version(), ...options?.query });
}

export function useVersionSuspense<TData = { data: VersionOut }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: VersionOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: versionKey(), queryFn: () => version(), ...options?.query });
}

