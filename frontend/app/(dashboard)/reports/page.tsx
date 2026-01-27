"use client";

import { useAuth } from "@/contexts/AuthContext";

export default function ReportsPage() {
    const { token } = useAuth();
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

    const handleDownload = async () => {
        try {
            const res = await fetch(`${API_BASE}/reports/shipments_export`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "shipments_export.xlsx";
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (e) {
            console.error("Download failed", e);
            alert("Failed to download report");
        }
    };

    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold">Rapports</h2>
            <div className="rounded-lg border bg-white p-6 shadow-sm">
                <h3 className="text-lg font-medium text-gray-900">Export des Expéditions</h3>
                <p className="mt-1 text-sm text-gray-500">
                    Téléchargez une liste complète de toutes les expéditions et leur statut actuel au format Excel.
                </p>
                <div className="mt-5">
                    <button
                        onClick={handleDownload}
                        className="inline-flex items-center rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors"
                    >
                        Télécharger .xlsx
                    </button>
                </div>
            </div>
        </div>
    );
}
