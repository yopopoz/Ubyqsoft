/**
 * Types centralisés pour le Logistics Chatbot & Dashboard
 * Synchronisés avec le backend Python (models.py)
 */

export * from "./event";
export * from "./shipment";

// ============================================
// User Interface
// ============================================
export interface User {
    id: number;
    email: string;
    name?: string | null;
    role: "client" | "ops" | "admin";
    created_at?: string | null;
}

export interface UserCreate {
    email: string;
    password: string;
    name?: string | null;
    role?: "client" | "ops" | "admin";
}

// ============================================
// Auth Types
// ============================================
export interface TokenResponse {
    access_token: string;
    token_type: string;
}

export interface AuthContextType {
    user: User | null;
    token: string | null;
    isLoggedIn: boolean;
    canWrite: boolean;
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
}

// ============================================
// Helper Functions - Others
// ============================================

/**
 * Retourne une couleur de badge en fonction du statut
 */
export function getStatusColor(status: string | null | undefined): { bg: string; text: string } {
    if (!status) return { bg: "bg-surface-1", text: "text-slate-600" };

    // Mappage des couleurs utilisant les nouvelles variables CSS si possible ou des classes Tailwind standard
    // Note: On utilise des classes Tailwind standard pour la compatibilité immédiate
    const statusColors: Record<string, { bg: string; text: string }> = {
        ORDER_INFO: { bg: "bg-slate-100", text: "text-slate-600" },
        PRODUCTION_READY: { bg: "bg-slate-100", text: "text-slate-600" },
        LOADING_IN_PROGRESS: { bg: "bg-amber-50", text: "text-amber-700" },
        SEAL_NUMBER_CUTOFF: { bg: "bg-slate-100", text: "text-slate-600" },
        EXPORT_CLEARANCE_CAMBODIA: { bg: "bg-slate-100", text: "text-slate-600" },
        TRANSIT_OCEAN: { bg: "bg-brand-secondary/5", text: "text-brand-secondary" },
        TRANSIT_PORT_OF_LOADING: { bg: "bg-brand-secondary/5", text: "text-brand-secondary" },
        TRANSIT_PORT_OF_DISCHARGE: { bg: "bg-brand-secondary/5", text: "text-brand-secondary" },
        "ON BOARD": { bg: "bg-brand-secondary/5", text: "text-brand-secondary" },
        "ON_BOARD": { bg: "bg-brand-secondary/5", text: "text-brand-secondary" },
        ARRIVAL_PORT_NYNJ: { bg: "bg-brand-secondary/5", text: "text-brand-secondary" },
        IMPORT_CLEARANCE_CBP: { bg: "bg-slate-100", text: "text-slate-600" },
        CUSTOMS_CLEARANCE: { bg: "bg-amber-50", text: "text-amber-700" },
        FINAL_DELIVERY: { bg: "bg-emerald-50", text: "text-emerald-700" },
        CONTAINER_DEPARTURE_FACTORY: { bg: "bg-brand-secondary/5", text: "text-brand-secondary" },
        BILL_OF_LADING_RELEASED: { bg: "bg-slate-100", text: "text-slate-600" },
    };
    return statusColors[status] || { bg: "bg-slate-100", text: "text-slate-600" };
}

export function getStatusVariant(status: string | null | undefined): "neutral" | "success" | "warning" | "error" | "info" | "brand" {
    if (!status) return "neutral";
    if (status === "FINAL_DELIVERY") return "success";
    if (status === "PROACTIVE_ALERT") return "error";
    if (status === "LOADING_IN_PROGRESS") return "warning";
    if (status.includes("TRANSIT") || status.includes("ON BOARD") || status === "ON_BOARD") return "brand"; // Changed to brand/primary for transit
    if (status === "PRODUCTION_READY") return "info";
    return "neutral";
}
