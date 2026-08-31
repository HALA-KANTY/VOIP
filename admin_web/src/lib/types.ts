// Les champs Decimal du backend (Pydantic v2) sont serialises en chaine (ex: "12.50"),
// pas en nombre : on les type donc en `string` et on les convertit a l'affichage.

export type StatutUtilisateur = "actif" | "inactif" | "suspendu";
export type StatutCDR = "termine" | "echoue" | "coupe" | "occupe" | "sans_reponse" | "hors_ligne";
export type StatutToken = "non_utilise" | "utilise";

export interface Utilisateur {
  id: number;
  username: string;
  nom_complet: string;
  email: string | null;
  sip_id: string | null;
  sip_secret: string | null;
  solde: string;
  statut: StatutUtilisateur;
  date_creation: string;
  type_utilisateur: "normal" | "commercial" | "support" | "comptabilite";
}

export interface UtilisateurCreate {
  username: string;
  nom_complet: string;
  email?: string | null;
  sip_id?: string | null;
  sip_secret?: string | null;
  password: string;
  type_utilisateur?: "normal" | "commercial" | "support" | "comptabilite";
}

export interface UtilisateurUpdate {
  nom_complet?: string;
  email?: string | null;
  sip_id?: string | null;
  sip_secret?: string | null;
  statut?: StatutUtilisateur;
  type_utilisateur?: "normal" | "commercial" | "support" | "comptabilite";
}

export interface CDR {
  id: number;
  utilisateur_id: number;
  utilisateur_nom: string;
  date_appel: string;
  duree: number;
  destination: string;
  cout: string;
  statut: StatutCDR;
  type_connexion: string;
}

export interface CDRFiltres {
  date_debut?: string;
  date_fin?: string;
  utilisateur_id?: number;
  destination?: string;
  duree_min?: number;
  duree_max?: number;
  cout_min?: number;
  cout_max?: number;
}

export interface Token {
  id: number;
  code: string;
  montant: string;
  statut: StatutToken;
  date_creation: string;
  date_utilisation: string | null;
}

export interface Rechargement {
  id: number;
  utilisateur_id: number;
  token_id: number;
  montant: string;
  date_rechargement: string;
}

export interface StatistiquesAppels {
  total_appels: number;
  appels_termines: number;
  appels_echoues: number;
  appels_coupes: number;
  duree_totale_secondes: number;
  duree_moyenne_secondes: number;
}

export interface RevenuParPeriode {
  periode: string;
  revenu: string;
}

export interface StatistiquesUtilisateurs {
  total_utilisateurs: number;
  utilisateurs_actifs: number;
  utilisateurs_suspendus: number;
  solde_total: string;
}

export interface TopDestination {
  destination: string;
  nombre_appels: number;
  cout_total: string;
}

export interface ServiceIVR {
  id: number;
  nom: string;
  code: string;
  type: string;
  destination: string;
  description: string | null;
  actif: boolean;
  date_creation: string;
}

export interface ServiceIVRCreate {
  nom: string;
  code: string;
  type: string;
  destination: string;
  description?: string;
}

export interface ServiceIVRUpdate {
  nom?: string;
  code?: string;
  type?: string;
  destination?: string;
  description?: string | null;
  actif?: boolean;
}

export interface ResumeMonitoring {
  ami_connecte: boolean;
  total_utilisateurs: number;
  utilisateurs_actifs: number;
  appels_en_cours: number;
  details_appels: Array<{
    channel: string;
    utilisateur_id: number;
    utilisateur_nom: string;
    secondes_ecoulees: number;
    solde_initial: string;
    tarif: string;
  }>;
}

export interface BulkTokenRequest {
  montant: string;
  quantite: number;
}

