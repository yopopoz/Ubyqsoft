"use client";

import { useEffect, useState, useRef, useMemo } from "react";
import { Link } from "@/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { shipmentService } from "@/services/shipmentService";
import { Shipment } from "@/types/shipment";
import { EventType } from "@/types/event";
import { getStatusColor, formatEventType, getStatusVariant } from "@/types/index";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { useTranslations } from "next-intl";

// Helper for relative timestamps
// Helper for relative timestamps
function getTimeAgo(dateString: string | null | undefined, t: any) {
    if (!dateString) return "-";
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return t('today');
    if (diffDays === 1) return t('tomorrow');
    if (diffDays === -1) return t('yesterday');
    if (diffDays > 0 && diffDays < 7) return t('inDays', { days: diffDays });
    if (diffDays < 0 && diffDays > -7) return t('daysAgo', { days: Math.abs(diffDays) });

    return date.toLocaleDateString();
}

export default function ShipmentsTable() {
    const t = useTranslations('ShipmentsTable');
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
                setError(t('errorLoad'));
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

    if (loading) return <div className="p-8 text-center text-slate-600 animate-pulse">{t('loadingData')}</div>;
    if (error) return <div className="p-8 text-center text-status-error">{error}</div>;

    return (
        <div className="space-y-4">
            {/* Toolbar */}
            <div className="flex justify-end items-center mb-4">
                <div className="relative">
                    <button
                        onClick={() => setShowColumnSelector(!showColumnSelector)}
                        className="btn btn-secondary text-sm bg-white border border-surface-3 hover:bg-surface-1"
                    >
                        <svg className="w-4 h-4 mr-2 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 01-2 2h2a2 2 0 012-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 01-2 2h2a2 2 0 012-2M9 7a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        {t('columns')}
                    </button>

                    {showColumnSelector && (
                        <div className="absolute right-0 mt-2 w-48 bg-white border border-surface-3 shadow-lg rounded-lg p-2 z-50 animate-scale-in">
                            <div className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2 px-2">{t('display')}</div>
                            {Object.keys(visibleColumns).map((col) => (
                                <label key={col} className="flex items-center px-2 py-1.5 hover:bg-surface-1 rounded cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={visibleColumns[col as keyof typeof visibleColumns]}
                                        onChange={() => handleToggleColumn(col as keyof typeof visibleColumns)}
                                        className="rounded border-slate-300 text-brand-primary focus:ring-brand-primary mr-2"
                                    />
                                    <span className="text-sm capitalize text-slate-700">{t(col)}</span>
                                </label>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Desktop Smart Table */}
            <div className="hidden lg:block overflow-x-auto rounded-xl border border-surface-3 shadow-sm bg-white/80 backdrop-blur-sm scrollbar-thin scrollbar-thumb-slate-200 scrollbar-track-transparent">
                <table className="min-w-full w-max">
                    <thead className="bg-surface-1 border-b border-surface-2">
                        <tr>
                            {visibleColumns.reference && <th className="px-4 py-3 text-left text-sm font-bold text-slate-700 uppercase tracking-wider whitespace-nowrap">{t('reference')}</th>}
                            {visibleColumns.status && <th className="px-4 py-3 text-left text-sm font-bold text-slate-700 uppercase tracking-wider whitespace-nowrap">{t('status')}</th>}
                            {visibleColumns.route && <th className="px-4 py-3 text-left text-sm font-bold text-slate-700 uppercase tracking-wider whitespace-nowrap">{t('route')}</th>}
                            {visibleColumns.dates && <th className="px-4 py-3 text-left text-sm font-bold text-slate-700 uppercase tracking-wider whitespace-nowrap">{t('dates')}</th>}
                            {visibleColumns.mad_its && <th className="px-4 py-3 text-left text-sm font-bold text-slate-700 uppercase tracking-wider whitespace-nowrap">{t('mad_its')}</th>}
                            {visibleColumns.vessel && <th className="px-4 py-3 text-left text-sm font-bold text-slate-700 uppercase tracking-wider whitespace-nowrap">{t('vessel')}</th>}
                            {visibleColumns.forwarder_ref && <th className="px-4 py-3 text-left text-sm font-bold text-slate-700 uppercase tracking-wider whitespace-nowrap">{t('forwarder_ref')}</th>}
                            {visibleColumns.incoterm && <th className="px-4 py-3 text-left text-sm font-bold text-slate-700 uppercase tracking-wider whitespace-nowrap">{t('incoterm')}</th>}
                            {visibleColumns.sku && <th className="px-4 py-3 text-left text-sm font-bold text-slate-700 uppercase tracking-wider whitespace-nowrap">{t('sku')}</th>}
                            {visibleColumns.quantity && <th className="px-4 py-3 text-right text-sm font-bold text-slate-700 uppercase tracking-wider whitespace-nowrap">{t('quantity')}</th>}
                            <th className="px-4 py-3 text-right text-sm font-bold text-slate-700 uppercase tracking-wider whitespace-nowrap sticky right-0 bg-surface-1 shadow-[-4px_0_8px_-4px_rgba(0,0,0,0.05)]">{t('action')}</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-2">
                        {shipments.map((shipment) => (
                            <tr key={shipment.id} className="hover:bg-surface-1/50 transition-colors group">
                                {visibleColumns.reference && (
                                    <td className="px-4 py-3 whitespace-nowrap">
                                        <div className="flex flex-col">
                                            <span className="font-semibold text-brand-primary text-sm group-hover:text-brand-secondary transition-colors">
                                                {shipment.reference}
                                            </span>
                                            <span className="text-xs text-slate-600 uppercase tracking-wide max-w-[120px] truncate">{shipment.customer || "N/A"}</span>
                                        </div>
                                    </td>
                                )}
                                {visibleColumns.status && (
                                    <td className="px-4 py-3 whitespace-nowrap">
                                        <div className="scale-90 origin-left">
                                            <StatusBadge status={shipment.status} />
                                        </div>
                                    </td>
                                )}
                                {visibleColumns.route && (
                                    <td className="px-4 py-3 whitespace-nowrap">
                                        <div className="flex items-center text-sm text-slate-800">
                                            <span className="font-medium max-w-[80px] truncate" title={shipment.origin || ""}>{shipment.origin?.split(',')[0] || "-"}</span>
                                            <svg className="w-3 h-3 mx-1.5 text-slate-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
                                            <span className="font-medium max-w-[80px] truncate" title={shipment.destination || ""}>{shipment.destination?.split(',')[0] || "-"}</span>
                                        </div>
                                    </td>
                                )}
                                {visibleColumns.dates && (
                                    <td className="px-4 py-3 whitespace-nowrap">
                                        <div className="flex flex-col text-sm gap-0.5">
                                            <div className="flex items-center gap-2">
                                                <span className="text-slate-600 w-6 text-xs uppercase">{t('dep')}</span>
                                                <span className="text-black font-medium">{getTimeAgo(shipment.planned_etd, t)}</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className="text-slate-600 w-6 text-xs uppercase">{t('arr')}</span>
                                                <span className="text-black font-medium">{getTimeAgo(shipment.planned_eta, t)}</span>
                                            </div>
                                        </div>
                                    </td>
                                )}
                                {visibleColumns.mad_its && (
                                    <td className="px-4 py-3 whitespace-nowrap">
                                        <div className="flex flex-col text-sm gap-0.5">
                                            <div className="flex items-center gap-2">
                                                <span className="text-slate-600 w-6 text-xs uppercase">MAD</span>
                                                <span className="text-black font-medium">{shipment.mad_date ? new Date(shipment.mad_date).toLocaleDateString() : "-"}</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className="text-slate-600 w-6 text-xs uppercase">ITS</span>
                                                <span className="text-black font-medium">{shipment.its_date ? new Date(shipment.its_date).toLocaleDateString() : "-"}</span>
                                            </div>
                                        </div>
                                    </td>
                                )}
                                {visibleColumns.vessel && (
                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-800">
                                        <div className="flex flex-col max-w-[140px]">
                                            <span className="font-medium text-black truncate" title={shipment.vessel || ""}>{shipment.vessel || "-"}</span>
                                            {shipment.bl_number && <span className="text-xs text-slate-600 truncate">BL: {shipment.bl_number}</span>}
                                        </div>
                                    </td>
                                )}
                                {visibleColumns.forwarder_ref && (
                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-800">
                                        {shipment.forwarder_ref ? (
                                            <span className="bg-slate-50 px-1.5 py-0.5 rounded text-xs text-slate-700 font-mono border border-slate-200">{shipment.forwarder_ref}</span>
                                        ) : "-"}
                                    </td>
                                )}
                                {visibleColumns.incoterm && (
                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-800">
                                        <span className="bg-surface-2 px-1.5 py-0.5 rounded border border-surface-3 text-xs font-medium">{shipment.incoterm}</span>
                                    </td>
                                )}
                                {visibleColumns.sku && (
                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-700 max-w-[100px] truncate" title={shipment.sku || ""}>
                                        {shipment.sku || "-"}
                                    </td>
                                )}
                                {visibleColumns.quantity && (
                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-800 text-right font-mono">
                                        {shipment.quantity?.toLocaleString() || "-"}
                                    </td>
                                )}
                                <td className="px-4 py-3 whitespace-nowrap text-right text-xs font-medium sticky right-0 bg-white group-hover:bg-slate-50/50 shadow-[-4px_0_8px_-4px_rgba(0,0,0,0.05)] transition-colors">
                                    <Link href={`/shipment/${shipment.id}`} className="p-1.5 rounded-lg text-slate-400 hover:text-brand-secondary hover:bg-brand-secondary/5 transition-all inline-flex items-center justify-center">
                                        <span className="sr-only">{t('view')}</span>
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5l7 7-7 7" />
                                        </svg>
                                    </Link>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {shipments.length === 0 && (
                    <div className="p-12 text-center text-slate-600">
                        {t('noShipments')}
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
                                    <div className="text-xs text-slate-600 uppercase tracking-wide">{shipment.customer}</div>
                                </div>
                                <StatusBadge status={shipment.status} />
                            </div>

                            <div className="grid grid-cols-2 gap-2 text-sm text-slate-900 mb-3 bg-surface-1 p-2 rounded-lg">
                                <div>
                                    <span className="text-xs text-slate-600 block">{t('origin')}</span>
                                    {shipment.origin?.split(',')[0]}
                                </div>
                                <div className="text-right">
                                    <span className="text-xs text-slate-600 block">{t('destination')}</span>
                                    {shipment.destination?.split(',')[0]}
                                </div>
                            </div>

                            <div className="flex justify-between items-center text-sm text-slate-700 border-t border-surface-2 pt-2 mt-2">
                                <span>ETA: {getTimeAgo(shipment.planned_eta, t)}</span>
                                <span className="text-brand-secondary font-medium">{t('viewDetails')}</span>
                            </div>
                        </Link>
                    </Card>
                ))}
            </div>
        </div>
    );
}

