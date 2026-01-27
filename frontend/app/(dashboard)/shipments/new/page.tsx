"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { ShipmentCreate } from "@/types";

const INCOTERM_OPTIONS = [
    "FOB", "EXW", "FCA", "FAS", "CFR", "CIF", "CPT", "CIP", "DAP", "DPU", "DDP"
];

export default function NewShipmentPage() {
    const { token } = useAuth();
    const router = useRouter();
    const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

    const [form, setForm] = useState<ShipmentCreate>({
        reference: "",
        customer: "",
        origin: "",
        destination: "",
        incoterm: "FOB",
        planned_etd: null,
        planned_eta: null,
        container_number: null,
        seal_number: null,
        sku: null,
        quantity: null,
        weight_kg: null,
        volume_cbm: null,
    });

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleChange = (field: keyof ShipmentCreate, value: string | number | null) => {
        setForm(prev => ({ ...prev, [field]: value || null }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            const payload = {
                ...form,
                planned_etd: form.planned_etd ? new Date(form.planned_etd).toISOString() : null,
                planned_eta: form.planned_eta ? new Date(form.planned_eta).toISOString() : null,
                quantity: form.quantity ? Number(form.quantity) : null,
                weight_kg: form.weight_kg ? Number(form.weight_kg) : null,
                volume_cbm: form.volume_cbm ? Number(form.volume_cbm) : null,
            };

            const res = await fetch(`${API_BASE}/shipments`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                    "X-API-Key": "dev"
                },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Échec de la création de l'expédition");
            }

            router.push("/shipments");
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Une erreur est survenue";
            setError(message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center gap-4">
                <button
                    onClick={() => router.back()}
                    className="text-slate-500 hover:text-slate-700 transition-colors"
                >
                    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                    </svg>
                </button>
                <h2 className="text-2xl font-bold text-slate-900">Nouvelle expédition</h2>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Informations de base */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                        <svg className="h-5 w-5 text-brand-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Informations générales
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                Référence / N° de commande <span className="text-red-500">*</span>
                            </label>
                            <input
                                type="text"
                                required
                                placeholder="ex: PO-2026-001"
                                className="block w-full rounded-lg border border-slate-300 px-4 py-2.5 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-colors"
                                value={form.reference}
                                onChange={(e) => handleChange("reference", e.target.value)}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Client</label>
                            <input
                                type="text"
                                placeholder="Nom du client"
                                className="block w-full rounded-lg border border-slate-300 px-4 py-2.5 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-colors"
                                value={form.customer || ""}
                                onChange={(e) => handleChange("customer", e.target.value)}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Origine</label>
                            <input
                                type="text"
                                placeholder="ex: Phnom Penh, Cambodge"
                                className="block w-full rounded-lg border border-slate-300 px-4 py-2.5 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-colors"
                                value={form.origin || ""}
                                onChange={(e) => handleChange("origin", e.target.value)}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Destination</label>
                            <input
                                type="text"
                                placeholder="ex: New York/New Jersey, USA"
                                className="block w-full rounded-lg border border-slate-300 px-4 py-2.5 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-colors"
                                value={form.destination || ""}
                                onChange={(e) => handleChange("destination", e.target.value)}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Incoterm</label>
                            <select
                                className="block w-full rounded-lg border border-slate-300 px-4 py-2.5 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-colors bg-white"
                                value={form.incoterm || "FOB"}
                                onChange={(e) => handleChange("incoterm", e.target.value)}
                            >
                                {INCOTERM_OPTIONS.map(term => (
                                    <option key={term} value={term}>{term}</option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">SKU / Produit</label>
                            <input
                                type="text"
                                placeholder="SKU ou description du produit"
                                className="block w-full rounded-lg border border-slate-300 px-4 py-2.5 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-colors"
                                value={form.sku || ""}
                                onChange={(e) => handleChange("sku", e.target.value)}
                            />
                        </div>
                    </div>
                </div>

                {/* Détails du conteneur et de l'expédition */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                        <svg className="h-5 w-5 text-brand-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                        </svg>
                        Détails du conteneur
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">N° de conteneur</label>
                            <input
                                type="text"
                                placeholder="ex: MAEU1234567"
                                className="block w-full rounded-lg border border-slate-300 px-4 py-2.5 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-colors font-mono"
                                value={form.container_number || ""}
                                onChange={(e) => handleChange("container_number", e.target.value)}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">N° de scellé</label>
                            <input
                                type="text"
                                placeholder="Numéro du scellé"
                                className="block w-full rounded-lg border border-slate-300 px-4 py-2.5 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-colors font-mono"
                                value={form.seal_number || ""}
                                onChange={(e) => handleChange("seal_number", e.target.value)}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Quantité (unités)</label>
                            <input
                                type="number"
                                min="0"
                                placeholder="Nombre d'unités"
                                className="block w-full rounded-lg border border-slate-300 px-4 py-2.5 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-colors"
                                value={form.quantity || ""}
                                onChange={(e) => handleChange("quantity", e.target.value ? parseInt(e.target.value) : null)}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Poids (kg)</label>
                            <input
                                type="number"
                                min="0"
                                step="0.01"
                                placeholder="Poids total en kilogrammes"
                                className="block w-full rounded-lg border border-slate-300 px-4 py-2.5 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-colors"
                                value={form.weight_kg || ""}
                                onChange={(e) => handleChange("weight_kg", e.target.value ? parseFloat(e.target.value) : null)}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Volume (m³)</label>
                            <input
                                type="number"
                                min="0"
                                step="0.01"
                                placeholder="Mètres cubes"
                                className="block w-full rounded-lg border border-slate-300 px-4 py-2.5 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-colors"
                                value={form.volume_cbm || ""}
                                onChange={(e) => handleChange("volume_cbm", e.target.value ? parseFloat(e.target.value) : null)}
                            />
                        </div>
                    </div>
                </div>

                {/* Planning */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                        <svg className="h-5 w-5 text-brand-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        Planning
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                Date de départ prévue
                                <span className="text-slate-400 font-normal ml-1">(ETD)</span>
                            </label>
                            <input
                                type="datetime-local"
                                className="block w-full rounded-lg border border-slate-300 px-4 py-2.5 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-colors"
                                value={form.planned_etd || ""}
                                onChange={(e) => handleChange("planned_etd", e.target.value)}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                Date d'arrivée prévue
                                <span className="text-slate-400 font-normal ml-1">(ETA)</span>
                            </label>
                            <input
                                type="datetime-local"
                                className="block w-full rounded-lg border border-slate-300 px-4 py-2.5 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-colors"
                                value={form.planned_eta || ""}
                                onChange={(e) => handleChange("planned_eta", e.target.value)}
                            />
                        </div>
                    </div>
                </div>

                {/* Message d'erreur */}
                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
                        <svg className="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                        {error}
                    </div>
                )}

                {/* Actions */}
                <div className="flex justify-end gap-3 pt-4">
                    <button
                        type="button"
                        onClick={() => router.back()}
                        className="rounded-lg px-6 py-2.5 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
                    >
                        Annuler
                    </button>
                    <button
                        type="submit"
                        disabled={loading || !form.reference}
                        className="rounded-lg bg-brand-primary px-6 py-2.5 text-sm font-medium text-white shadow-lg shadow-brand-primary/10 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-primary/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95"
                    >
                        {loading ? (
                            <span className="flex items-center gap-2">
                                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                </svg>
                                Création en cours...
                            </span>
                        ) : (
                            "Créer l'expédition"
                        )}
                    </button>
                </div>
            </form>
        </div>
    );
}
