// ============================================
// EventType Enum - Tous les jalons possibles
// ============================================
export const EventType = {
    // Production / Chargement / Scellé / Export / Transit / Arrivée / Import / Livraison
    PRODUCTION_READY: "PRODUCTION_READY",
    LOADING_IN_PROGRESS: "LOADING_IN_PROGRESS",
    SEAL_NUMBER_CUTOFF: "SEAL_NUMBER_CUTOFF",
    EXPORT_CLEARANCE_CAMBODIA: "EXPORT_CLEARANCE_CAMBODIA",
    TRANSIT_OCEAN: "TRANSIT_OCEAN",
    ARRIVAL_PORT_NYNJ: "ARRIVAL_PORT_NYNJ",
    IMPORT_CLEARANCE_CBP: "IMPORT_CLEARANCE_CBP",
    FINAL_DELIVERY: "FINAL_DELIVERY",

    // Opérationnels
    ORDER_INFO: "ORDER_INFO",
    CONTAINER_READY_FOR_DEPARTURE: "CONTAINER_READY_FOR_DEPARTURE",
    PHOTOS_CONTAINER_WEIGHT: "PHOTOS_CONTAINER_WEIGHT",
    GPS_POSITION_ETA_ETD: "GPS_POSITION_ETA_ETD",
    UNLOADING_GATE_OUT: "UNLOADING_GATE_OUT",
    CUSTOMS_STATUS_DECLARATION: "CUSTOMS_STATUS_DECLARATION",
    UNLOADING_TIME_CHECKS: "UNLOADING_TIME_CHECKS",

    // Système
    LOGISTICS_DB_UPDATE: "LOGISTICS_DB_UPDATE",
    CHATBOT_QUERY: "CHATBOT_QUERY",
    REALTIME_DASHBOARD: "REALTIME_DASHBOARD",
    PROACTIVE_ALERT: "PROACTIVE_ALERT",
    REPORTING_ANALYTICS: "REPORTING_ANALYTICS",
    USERS_CLIENT: "USERS_CLIENT",
    USERS_LOGISTICS: "USERS_LOGISTICS",
} as const;

export type EventTypeKey = keyof typeof EventType;
export type EventTypeValue = typeof EventType[EventTypeKey];

// Liste des EventTypes regroupés par catégorie pour l'UI
export const EVENT_TYPE_CATEGORIES = {
    "Production & Chargement": [
        EventType.PRODUCTION_READY,
        EventType.LOADING_IN_PROGRESS,
        EventType.SEAL_NUMBER_CUTOFF,
    ],
    "Export & Transit": [
        EventType.EXPORT_CLEARANCE_CAMBODIA,
        EventType.TRANSIT_OCEAN,
        EventType.CONTAINER_READY_FOR_DEPARTURE,
    ],
    "Arrivée & Import": [
        EventType.ARRIVAL_PORT_NYNJ,
        EventType.IMPORT_CLEARANCE_CBP,
        EventType.FINAL_DELIVERY,
    ],
    "Opérationnels": [
        EventType.ORDER_INFO,
        EventType.PHOTOS_CONTAINER_WEIGHT,
        EventType.GPS_POSITION_ETA_ETD,
        EventType.UNLOADING_GATE_OUT,
        EventType.CUSTOMS_STATUS_DECLARATION,
        EventType.UNLOADING_TIME_CHECKS,
    ],
    "Système": [
        EventType.LOGISTICS_DB_UPDATE,
        EventType.CHATBOT_QUERY,
        EventType.REALTIME_DASHBOARD,
        EventType.PROACTIVE_ALERT,
        EventType.REPORTING_ANALYTICS,
        EventType.USERS_CLIENT,
        EventType.USERS_LOGISTICS,
    ],
};

// ============================================
// Event Interface - Jalon
// ============================================
export interface Event {
    id: number;
    shipment_id: number;
    type: EventTypeValue;
    timestamp: string; // ISO datetime string
    payload?: Record<string, unknown> | null; // Données brutes: GPS, preuve photo, doc URLs...
    note?: string | null;
    critical: boolean; // Faciliter les alertes
}

export interface EventCreate {
    shipment_id: number;
    type: EventTypeValue;
    payload?: Record<string, unknown> | null;
    note?: string | null;
    critical?: boolean;
    timestamp?: string | null;
}

// ============================================
// Helper Functions
// ============================================

/**
 * Formatte un EventType pour l'affichage (remplace _ par espaces)
 */
export function formatEventType(eventType: string | null | undefined): string {
    if (!eventType) return "Unknown";
    return eventType.replace(/_/g, " ");
}

/**
 * Vérifie si un événement est critique
 */
export function isCriticalEvent(eventType: string | null | undefined): boolean {
    if (!eventType) return false;

    const criticalTypes: string[] = [
        EventType.PROACTIVE_ALERT,
        EventType.CUSTOMS_STATUS_DECLARATION,
        EventType.IMPORT_CLEARANCE_CBP,
    ];
    return criticalTypes.includes(eventType);
}
