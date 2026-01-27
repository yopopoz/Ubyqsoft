"use client";

import { useEffect, useState, useRef, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { shipmentService } from "@/services/shipmentService";
import { Shipment } from "@/types/shipment";
import { EventType } from "@/types/event";
import { getStatusColor, formatEventType, getStatusVariant } from "@/types/index";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";

// Helper for relative timestamps
function getTimeAgo(dateString: string | null | undefined) {
    if (!dateString) return "-";
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Aujourd'hui";
    if (diffDays === 1) return "Demain";
    if (diffDays === -1) return "Hier";
    if (diffDays > 0 && diffDays < 7) return `Dans ${diffDays} jours`;
    if (diffDays < 0 && diffDays > -7) return `Il y a ${Math.abs(diffDays)} jours`;

    return date.toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
}

export default function ShipmentsTable() {
    const [shipments, setShipments] = useState<Shipment[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { token, logout } = useAuth();
    const wsRef = useRef<WebSocket | null>(null);
    const [flashingRows, setFlashingRows] = useState<Set<number>>(new Set());

    // UI State
    const [visibleColumns, setVisibleColumns] = useState({
        reference: true,
        status: true,
        route: true,
        dates: true,
        mad_its: false, // New: MAD & ITS Dates
        vessel: false,  // New: Vessel & BL
        forwarder_ref: false, // New: Forwarder Ref
        incoterm: false,
        sku: false,
        quantity: false,
    });
    const [showColumnSelector, setShowColumnSelector] = useState(false);

    useEffect(() => {
        if (!token) return;
        loadShipments();

        // WebSocket Login
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";
        const wsUrl = API_BASE.replace("http", "ws") + "/ws/shipments";

        try {
            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onopen = () => console.log("🟢 WS Connected");
            ws.onmessage = async (event) => {
                const message = event.data;
                console.log("⚡ WS Message:", message);

                if (message.startsWith("event_created")) {
                    await loadShipments(); // Refresh data
                }
            };

            return () => {
                if (ws.readyState === 1) ws.close();
            };
        } catch (e) {
            console.error("WS Connection failed", e);
        }
    }, [token]);

    const loadShipments = async () => {
        try {
            if (!token) return;
            const data = await shipmentService.getAll(token);
            // Sort by recently updated or created
            const sorted = data.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
            setShipments(sorted);
        } catch (err: any) {
            console.error(err);
            // 401 is handled globally by AuthContext now
            if (err?.status !== 401) {
                setError("Impossible de charger les expéditions.");
            }
        } finally {
            setLoading(false);
        }
    };

    const handleToggleColumn = (key: keyof typeof visibleColumns) => {
        setVisibleColumns(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const StatusBadge = ({ status }: { status: string }) => {
        const variant = getStatusVariant(status);

        return (
            <Badge variant={variant} className="shadow-sm">
                {formatEventType(status)}
            </Badge>
        );
    };

    if (loading) return <div className="p-8 text-center text-slate-400 animate-pulse">Chargement des données...</div>;
    if (error) return <div className="p-8 text-center text-status-error">{error}</div>;

    return (
        <div className="space-y-4">
            {/* Toolbar */}
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-brand-primary">Tableau de Bord</h2>
                <div className="relative">
                    <button
                        onClick={() => setShowColumnSelector(!showColumnSelector)}
                        className="btn btn-secondary text-sm bg-white border border-surface-3 hover:bg-surface-1"
                    >
                        <svg className="w-4 h-4 mr-2 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 01-2 2h2a2 2 0 012-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 01-2 2h2a2 2 0 012-2M9 7a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        Colonnes
                    </button>

                    {showColumnSelector && (
                        <div className="absolute right-0 mt-2 w-48 bg-white border border-surface-3 shadow-lg rounded-lg p-2 z-50 animate-scale-in">
                            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 px-2">Affichage</div>
                            {Object.keys(visibleColumns).map((col) => (
                                <label key={col} className="flex items-center px-2 py-1.5 hover:bg-surface-1 rounded cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={visibleColumns[col as keyof typeof visibleColumns]}
                                        onChange={() => handleToggleColumn(col as keyof typeof visibleColumns)}
                                        className="rounded border-slate-300 text-brand-primary focus:ring-brand-primary mr-2"
                                    />
                                    <span className="text-sm capitalize text-slate-700">{col.replace(/_/g, ' ')}</span>
                                </label>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Desktop Smart Table */}
            <div className="hidden lg:block overflow-hidden rounded-xl border border-surface-3 shadow-sm bg-white/80 backdrop-blur-sm">
                <table className="min-w-full">
                    <thead className="bg-surface-1 border-b border-surface-2">
                        <tr>
                            {visibleColumns.reference && <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Référence</th>}
                            {visibleColumns.status && <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Statut</th>}
                            {visibleColumns.route && <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Trajet</th>}
                            {visibleColumns.dates && <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">ETD / ETA</th>}
                            {visibleColumns.mad_its && <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">MAD / ITS</th>}
                            {visibleColumns.vessel && <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Navire</th>}
                            {visibleColumns.forwarder_ref && <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Ref Transitaddy</th>}
                            {visibleColumns.incoterm && <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Incoterm</th>}
                            {visibleColumns.sku && <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">SKU</th>}
                            {visibleColumns.quantity && <th className="px-6 py-3 text-right text-xs font-bold text-slate-500 uppercase tracking-wider">Qté</th>}
                            <th className="px-6 py-3 text-right text-xs font-bold text-slate-500 uppercase tracking-wider">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-2">
                        {shipments.map((shipment) => (
                            <tr key={shipment.id} className="hover:bg-surface-1/50 transition-colors group">
                                {visibleColumns.reference && (
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex flex-col">
                                            <span className="font-semibold text-brand-primary group-hover:text-brand-secondary transition-colors">
                                                {shipment.reference}
                                            </span>
                                            <span className="text-xs text-slate-400">{shipment.customer || "N/A"}</span>
                                        </div>
                                    </td>
                                )}
                                {visibleColumns.status && (
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <StatusBadge status={shipment.status} />
                                    </td>
                                )}
                                {visibleColumns.route && (
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center text-sm text-slate-600">
                                            <span className="font-medium">{shipment.origin?.split(',')[0] || "-"}</span>
                                            <svg className="w-4 h-4 mx-2 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
                                            <span className="font-medium">{shipment.destination?.split(',')[0] || "-"}</span>
                                        </div>
                                    </td>
                                )}
                                {visibleColumns.dates && (
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex flex-col text-xs">
                                            <div className="flex justify-between w-32 mb-1">
                                                <span className="text-slate-400">ETD:</span>
                                                <span className="text-slate-700 font-medium">{getTimeAgo(shipment.planned_etd)}</span>
                                            </div>
                                            <div className="flex justify-between w-32">
                                                <span className="text-slate-400">ETA:</span>
                                                <span className="text-slate-700 font-medium">{getTimeAgo(shipment.planned_eta)}</span>
                                            </div>
                                        </div>
                                    </td>
                                )}
                                {visibleColumns.mad_its && (
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex flex-col text-xs">
                                            <div className="flex justify-between w-32 mb-1">
                                                <span className="text-slate-400">MAD:</span>
                                                <span className="text-slate-700 font-medium">{shipment.mad_date ? new Date(shipment.mad_date).toLocaleDateString() : "-"}</span>
                                            </div>
                                            <div className="flex justify-between w-32">
                                                <span className="text-slate-400">ITS:</span>
                                                <span className="text-slate-700 font-medium">{shipment.its_date ? new Date(shipment.its_date).toLocaleDateString() : "-"}</span>
                                            </div>
                                        </div>
                                    </td>
                                )}
                                {visibleColumns.vessel && (
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                                        <div className="flex flex-col">
                                            <span className="font-medium text-slate-700 truncate max-w-[150px]" title={shipment.vessel || ""}>{shipment.vessel || "-"}</span>
                                            <span className="text-xs text-slate-400">{shipment.bl_number ? `BL: ${shipment.bl_number}` : ""}</span>
                                        </div>
                                    </td>
                                )}
                                {visibleColumns.forwarder_ref && (
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                                        {shipment.forwarder_ref ? (
                                            <span className="bg-slate-100 px-2 py-0.5 rounded text-xs text-slate-500 font-mono border border-slate-200">{shipment.forwarder_ref}</span>
                                        ) : "-"}
                                    </td>
                                )}
                                {visibleColumns.incoterm && (
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                                        <span className="bg-surface-2 px-2 py-1 rounded border border-surface-3">{shipment.incoterm}</span>
                                    </td>
                                )}
                                {visibleColumns.sku && (
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                                        {shipment.sku || "-"}
                                    </td>
                                )}
                                {visibleColumns.quantity && (
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600 text-right font-mono">
                                        {shipment.quantity?.toLocaleString() || "-"}
                                    </td>
                                )}
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <Link href={`/shipment/${shipment.id}`} className="text-brand-secondary hover:text-brand-primary transition-colors font-semibold">
                                        Détails &rarr;
                                    </Link>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {shipments.length === 0 && (
                    <div className="p-12 text-center text-slate-500">
                        Aucune expédition trouvée.
                    </div>
                )}
            </div>

            {/* Mobile View (Stacked Cards) */}
            <div className="lg:hidden space-y-4">
                {shipments.map((shipment) => (
                    <Card key={shipment.id} hover className="border-l-4 border-l-brand-secondary">
                        <Link href={`/shipment/${shipment.id}`} className="block">
                            <div className="flex justify-between items-start mb-3">
                                <div>
                                    <div className="font-bold text-brand-primary">{shipment.reference}</div>
                                    <div className="text-xs text-slate-500">{shipment.customer}</div>
                                </div>
                                <StatusBadge status={shipment.status} />
                            </div>

                            <div className="grid grid-cols-2 gap-2 text-sm text-slate-600 mb-3 bg-surface-1 p-2 rounded-lg">
                                <div>
                                    <span className="text-xs text-slate-400 block">Origine</span>
                                    {shipment.origin?.split(',')[0]}
                                </div>
                                <div className="text-right">
                                    <span className="text-xs text-slate-400 block">Destination</span>
                                    {shipment.destination?.split(',')[0]}
                                </div>
                            </div>

                            <div className="flex justify-between items-center text-xs text-slate-500 border-t border-surface-2 pt-2 mt-2">
                                <span>ETA: {getTimeAgo(shipment.planned_eta)}</span>
                                <span className="text-brand-secondary font-medium">Voir détails</span>
                            </div>
                        </Link>
                    </Card>
                ))}
            </div>
        </div>
    );
}

