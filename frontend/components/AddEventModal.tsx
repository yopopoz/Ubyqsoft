"use client";

import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { EventType, EventTypeValue } from "@/types";

// Catégories d'événements traduites en français
const EVENT_TYPE_CATEGORIES_FR: Record<string, { value: EventTypeValue; label: string }[]> = {
    "Production & Chargement": [
        { value: EventType.PRODUCTION_READY, label: "Production terminée" },
        { value: EventType.LOADING_IN_PROGRESS, label: "Chargement en cours" },
        { value: EventType.SEAL_NUMBER_CUTOFF, label: "Scellé posé" },
    ],
    "Export & Transit": [
        { value: EventType.EXPORT_CLEARANCE_CAMBODIA, label: "Dédouanement export" },
        { value: EventType.TRANSIT_OCEAN, label: "Transit maritime" },
        { value: EventType.CONTAINER_READY_FOR_DEPARTURE, label: "Conteneur prêt au départ" },
    ],
    "Arrivée & Import": [
        { value: EventType.ARRIVAL_PORT_NYNJ, label: "Arrivée au port" },
        { value: EventType.IMPORT_CLEARANCE_CBP, label: "Dédouanement import" },
        { value: EventType.FINAL_DELIVERY, label: "Livraison finale" },
    ],
    "Opérationnels": [
        { value: EventType.ORDER_INFO, label: "Information commande" },
        { value: EventType.PHOTOS_CONTAINER_WEIGHT, label: "Photos & poids conteneur" },
        { value: EventType.GPS_POSITION_ETA_ETD, label: "Position GPS / ETA / ETD" },
        { value: EventType.UNLOADING_GATE_OUT, label: "Déchargement - Sortie porte" },
        { value: EventType.CUSTOMS_STATUS_DECLARATION, label: "Déclaration douanière" },
        { value: EventType.UNLOADING_TIME_CHECKS, label: "Contrôle temps déchargement" },
    ],

};

// --- Dynamic Fields Configuration ---
const getDynamicFields = (type: EventTypeValue) => {
    switch (type) {
        case EventType.SEAL_NUMBER_CUTOFF:
            return [{ name: "seal_number", label: "Numéro de Scellé", type: "text", placeholder: "Ex: JKL123456" }];
        case EventType.CONTAINER_READY_FOR_DEPARTURE:
            return [{ name: "container_number", label: "Numéro de Conteneur", type: "text", placeholder: "Ex: MSCU1234567" }];
        case EventType.PHOTOS_CONTAINER_WEIGHT:
            return [
                { name: "weight_kg", label: "Poids (kg)", type: "number", placeholder: "Ex: 15400" },
                { name: "photo_url", label: "Lien Photo (URL)", type: "text", placeholder: "https://..." }
            ];
        case EventType.GPS_POSITION_ETA_ETD:
            return [
                { name: "location", label: "Position Actuelle", type: "text", placeholder: "Ex: Port of Singapore" },
                { name: "new_eta", label: "Nouvelle ETA Estimée", type: "date" }
            ];
        case EventType.TRANSIT_OCEAN:
            return [
                { name: "vessel_name", label: "Navire", type: "text", placeholder: "Ex: MAERSK SEOUL" },
                { name: "voyage_ref", label: "Numéro de Voyage", type: "text", placeholder: "Ex: 042E" }
            ];
        default:
            return [];
    }
};

interface AddEventModalProps {
    shipmentId: number;
    onSuccess: () => void;
}

export default function AddEventModal({ shipmentId, onSuccess }: AddEventModalProps) {
    const { token } = useAuth();
    const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

    const [isOpen, setIsOpen] = useState(false);
    const [type, setType] = useState<EventTypeValue>(EventType.ORDER_INFO);
    const [date, setDate] = useState<string>(new Date().toISOString().slice(0, 16)); // Default to now (local datetime-local format)
    const [note, setNote] = useState("");
    const [payloadData, setPayloadData] = useState<Record<string, string>>({});
    const [critical, setCritical] = useState(false);
    const [loading, setLoading] = useState(false);

    // Update payload when type changes to clear irrelevant fields
    const handleTypeChange = (newType: EventTypeValue) => {
        setType(newType);
        setPayloadData({});
        // Default note based on type for speed
        if (newType === EventType.SEAL_NUMBER_CUTOFF) setNote("Scellé posé et vérifié.");
        if (newType === EventType.PHOTOS_CONTAINER_WEIGHT) setNote("Photos chargement et pesée effectuées.");
    };

    const handlePayloadChange = (key: string, value: string) => {
        setPayloadData(prev => ({ ...prev, [key]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const response = await fetch(`${API_BASE}/events/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                    "X-API-Key": "dev"
                },
                body: JSON.stringify({
                    shipment_id: shipmentId,
                    type: type,
                    timestamp: new Date(date).toISOString(),
                    payload: Object.keys(payloadData).length > 0 ? payloadData : null,
                    note: note || null,
                    critical: critical
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Échec de l'ajout de l'événement");
            }

            onSuccess();
            setIsOpen(false);
            // Réinitialiser le formulaire
            // Réinitialiser le formulaire
            setType(EventType.ORDER_INFO);
            setPayloadData({});
            setNote("");
            setCritical(false);
            setDate(new Date().toISOString().slice(0, 16));
        } catch (error: any) {
            console.error("Échec de l'ajout de l'événement", error);
            alert(`Erreur: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) {
        return (
            <button
                onClick={() => setIsOpen(true)}
                className="rounded-lg bg-brand-secondary px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-all shadow-lg shadow-brand-secondary/20 active:scale-95"
            >
                + Ajouter un événement
            </button>
        );
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-2xl animate-in fade-in zoom-in duration-200">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-slate-900">Nouvel événement</h3>
                    <button
                        onClick={() => setIsOpen(false)}
                        className="text-slate-400 hover:text-slate-600 transition-colors"
                    >
                        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                    {/* Type d'événement - Groupé par catégorie */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">
                            Type d'événement
                        </label>
                        <select
                            value={type}
                            onChange={(e) => handleTypeChange(e.target.value as EventTypeValue)}
                            className="block w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-slate-900 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-colors"
                        >
                            {Object.entries(EVENT_TYPE_CATEGORIES_FR).map(([category, events]) => (
                                <optgroup key={category} label={category}>
                                    {events.map((event) => (
                                        <option key={event.value} value={event.value}>
                                            {event.label}
                                        </option>
                                    ))}
                                </optgroup>
                            ))}
                        </select>
                    </div>

                    {/* Date de l'événement */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">
                            Date de l'événement
                        </label>
                        <input
                            type="datetime-local"
                            value={date}
                            onChange={(e) => setDate(e.target.value)}
                            className="block w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-slate-900 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-colors"
                        />
                    </div>

                    {/* Dynamic Fields Section */}
                    {getDynamicFields(type).length > 0 && (
                        <div className="bg-slate-50 p-4 rounded-lg border border-slate-100 space-y-4">
                            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">Données Spécifiques ({EVENT_TYPE_CATEGORIES_FR[Object.keys(EVENT_TYPE_CATEGORIES_FR).find(k => EVENT_TYPE_CATEGORIES_FR[k].some(e => e.value === type))!]?.find(e => e.value === type)?.label})</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {getDynamicFields(type).map((field) => (
                                    <div key={field.name} className={field.type === 'text' && getDynamicFields(type).length % 2 !== 0 && field.name === getDynamicFields(type)[getDynamicFields(type).length - 1].name ? "md:col-span-2" : ""}>
                                        <label className="block text-xs font-medium text-slate-700 mb-1">
                                            {field.label}
                                        </label>
                                        <input
                                            type={field.type}
                                            placeholder={field.placeholder}
                                            value={payloadData[field.name] || ""}
                                            onChange={(e) => handlePayloadChange(field.name, e.target.value)}
                                            className="block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-brand-secondary focus:ring-1 focus:ring-brand-secondary transition-colors"
                                        />
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Note */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">
                            Note (optionnel)
                        </label>
                        <textarea
                            value={note}
                            onChange={(e) => setNote(e.target.value)}
                            placeholder="Ajoutez des informations supplémentaires..."
                            rows={3}
                            className="block w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 placeholder-slate-400 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-colors resize-none"
                        />
                    </div>

                    {/* Événement critique */}
                    <div className="flex items-center gap-3">
                        <input
                            type="checkbox"
                            id="critical"
                            checked={critical}
                            onChange={(e) => setCritical(e.target.checked)}
                            className="h-5 w-5 rounded border-slate-300 text-red-600 focus:ring-red-500 transition-colors cursor-pointer"
                        />
                        <label htmlFor="critical" className="text-sm font-medium text-slate-700 cursor-pointer">
                            <span className="text-red-600">⚠️ Événement critique</span>
                            <span className="block text-xs text-slate-500">Marquer cet événement comme nécessitant une attention immédiate</span>
                        </label>
                    </div>

                    {/* Boutons d'action */}
                    <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                        <button
                            type="button"
                            onClick={() => setIsOpen(false)}
                            className="rounded-lg px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-100 transition-colors"
                        >
                            Annuler
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="rounded-lg bg-brand-primary px-5 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg active:scale-95"
                        >
                            {loading ? (
                                <span className="flex items-center gap-2">
                                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                    </svg>
                                    Enregistrement...
                                </span>
                            ) : (
                                "Enregistrer"
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
