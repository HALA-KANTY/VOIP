import axios from "axios";
import type {
  CDR,
  CDRFiltres,
  RevenuParPeriode,
  Rechargement,
  StatistiquesAppels,
  StatistiquesUtilisateurs,
  Token,
  TopDestination,
  Utilisateur,
  UtilisateurCreate,
  UtilisateurUpdate,
  ServiceIVR,
  ServiceIVRCreate,
  ServiceIVRUpdate,
  ResumeMonitoring,
  BulkTokenRequest
} from "./types";

const TOKEN_STORAGE_KEY = "voip_admin_token";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
});

api.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      clearStoredToken();
      if (window.location.pathname !== "/login") {
        // Hors d'un composant React (intercepteur axios) : pas de useRouter disponible ici,
        // et un rechargement complet reinitialise proprement l'etat de l'app apres un 401.
        // eslint-disable-next-line @next/next/no-location-assign-relative-destination
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export async function login(username: string, password: string): Promise<string> {
  const body = new URLSearchParams({ username, password });
  const { data } = await axios.post<{ access_token: string }>(
    `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/auth/login`,
    body,
    { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
  );
  return data.access_token;
}

export const utilisateursApi = {
  lister: () => api.get<Utilisateur[]>("/api/utilisateurs").then((r) => r.data),
  obtenir: (id: number) => api.get<Utilisateur>(`/api/utilisateurs/${id}`).then((r) => r.data),
  creer: (payload: UtilisateurCreate) =>
    api.post<Utilisateur>("/api/utilisateurs", payload).then((r) => r.data),
  modifier: (id: number, payload: UtilisateurUpdate) =>
    api.put<Utilisateur>(`/api/utilisateurs/${id}`, payload).then((r) => r.data),
  supprimer: (id: number) => api.delete(`/api/utilisateurs/${id}`),
  crediter: (id: number, montant: string) =>
    api.post(`/api/utilisateurs/${id}/crediter`, { montant }).then((r) => r.data),
  regenererSecretSip: (id: number) =>
    api.post<Utilisateur>(`/api/utilisateurs/${id}/regenerer_secret_sip`).then((r) => r.data),
  debiter: (id: number, montant: string) =>
    api.post(`/api/utilisateurs/${id}/debiter`, { montant }).then((r) => r.data),
};

export const cdrApi = {
  lister: (filtres: CDRFiltres = {}) =>
    api.get<CDR[]>("/api/cdr", { params: filtres }).then((r) => r.data),
  exporterUrl: (filtres: CDRFiltres = {}) => {
    const params = new URLSearchParams();
    Object.entries(filtres).forEach(([cle, valeur]) => {
      if (valeur !== undefined && valeur !== "") params.set(cle, String(valeur));
    });
    return `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/cdr/export?${params.toString()}`;
  },
};

export const tokensApi = {
  lister: () => api.get<Token[]>("/api/tokens").then((r) => r.data),
  generer: (montant: string) =>
    api.post<Token>("/api/tokens/generer", { montant }).then((r) => r.data),
  genererLot: (payload: BulkTokenRequest) =>
    api
      .post<{ succes: boolean; message: string; montant: string; codes: string[] }>('/api/tokens/bulk', payload)
      .then((r) => r.data),
  supprimer: (id: number) => api.delete(`/api/tokens/${id}`),
};


export const rechargementsApi = {
  lister: () => api.get<Rechargement[]>("/api/rechargements").then((r) => r.data),
  creer: (utilisateur_id: number, code_token: string) =>
    api.post<Rechargement>("/api/rechargements", { utilisateur_id, code_token }).then((r) => r.data),
};

export const statistiquesApi = {
  appels: () => api.get<StatistiquesAppels>("/api/statistiques/appels").then((r) => r.data),
  revenus: (date_debut?: string, date_fin?: string) =>
    api
      .get<RevenuParPeriode[]>("/api/statistiques/revenus", { params: { date_debut, date_fin } })
      .then((r) => r.data),
  utilisateurs: () =>
    api.get<StatistiquesUtilisateurs>("/api/statistiques/utilisateurs").then((r) => r.data),
  destinations: (limite = 10) =>
    api
      .get<TopDestination[]>("/api/statistiques/destinations", { params: { limite } })
      .then((r) => r.data),
};

export const servicesIvrApi = {
  lister: () => api.get<ServiceIVR[]>('/api/services-ivr').then(r => r.data),
  creer: (data: ServiceIVRCreate) => api.post<ServiceIVR>('/api/services-ivr', data).then(r => r.data),
  modifier: (id: number, data: ServiceIVRUpdate) =>
    api.put<ServiceIVR>(`/api/services-ivr/${id}`, data).then((r) => r.data),
  supprimer: (id: number) => api.delete(`/api/services-ivr/${id}`),
};

export const monitoringApi = {
  resume: () => api.get<ResumeMonitoring>('/api/monitoring/resume').then(r => r.data),
};

export const tarifsApi = {
  obtenirActif: () => api.get<{ montant_par_seconde: string }>("/api/tarifs/actif").then((r) => r.data),
  changer: (montant: string) => api.post("/api/tarifs", { montant_par_seconde: montant }).then((r) => r.data),
};

