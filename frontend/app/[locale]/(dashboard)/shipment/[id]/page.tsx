"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { shipmentService } from "@/services/shipmentService";
import { Shipment } from "@/types/shipment";
import { Event, EventType, EventTypeValue } from "@/types/event";
import { formatEventType, getStatusVariant } from "@/types/index";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader } from "@/components/ui/Card";
import AddEventModal from "@/components/AddEventModal";
import { useTranslations } from "next-intl";

// --- Utility Functions ---

function getTimeAgo(dateStr: string, t: any): string {
    const diff = Date.now() - new Date(dateStr).getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return t('timeAgo.days', { n: days });
    if (hours > 0) return t('timeAgo.hours', { n: hours });
    if (minutes > 0) return t('timeAgo.minutes', { n: minutes });
    return t('timeAgo.justNow');
}

function formatDate(dateStr?: string | Date | null): string {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString();
}

// --- Helper Components ---

function HealthBadge({ shipment }: { shipment: Shipment }) {
    const t = useTranslations('ShipmentDetails');
    if (!shipment.planned_eta) return null;

    const eta = new Date(shipment.planned_eta);
    const today = new Date();
    const daysLeft = Math.ceil((eta.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

    // Logic: 
    // - Red: Planned ETA passed and not delivered
    // - Orange: Less than 5 days left and still in early stages (Order/Production)
    // - Green: On track or Delivered

    // We cast to string for comparison if needed or keep using enum values
    const isLate = daysLeft < 0 && shipment.status !== EventType.FINAL_DELIVERY;
    const isRisky = daysLeft < 5 && daysLeft >= 0 && ([EventType.ORDER_INFO, EventType.PRODUCTION_READY] as EventTypeValue[]).includes(shipment.status as EventTypeValue);

    if (isLate) {
        return (
            <span className="bg-red-50 text-red-600 text-xs font-bold px-2 py-0.5 rounded border border-red-100 uppercase tracking-wide flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                {t('confirmedDelay')}
            </span>
        );
    }

    if (isRisky) {
        return (
            <span className="bg-orange-50 text-orange-600 text-xs font-bold px-2 py-0.5 rounded border border-orange-100 uppercase tracking-wide flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                {t('delayRisk')}
            </span>
        );
    }

    return (
        <span className="bg-emerald-50 text-emerald-600 text-xs font-bold px-2 py-0.5 rounded border border-emerald-100 uppercase tracking-wide flex items-center gap-1">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
            {t('healthyStatus')}
        </span>
    );
}

function PredictiveInsight({ shipment }: { shipment: Shipment }) {
    const t = useTranslations('ShipmentDetails');
    const tEvents = useTranslations('Events');
    const isRisky = shipment.planned_eta &&
        (new Date(shipment.planned_eta).getTime() - Date.now() < 5 * 24 * 60 * 60 * 1000) &&
        ([EventType.ORDER_INFO, EventType.PRODUCTION_READY] as EventTypeValue[]).includes(shipment.status as EventTypeValue);

    if (!isRisky) return null;

    return (
        <div className="bg-gradient-to-r from-orange-50 to-white p-4 rounded-xl border border-orange-100 mb-6 animate-pulse-slow">
            <div className="flex items-start gap-3">
                <div className="p-2 bg-white rounded-lg shadow-sm border border-orange-100 text-orange-500">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                </div>
                <div>
                    <h3 className="text-sm font-bold text-slate-800">{t('aiPrediction')}</h3>
                    <p className="text-xs text-slate-600 mt-1 leading-relaxed"
                        dangerouslySetInnerHTML={{ __html: t.raw('aiPredictionText', { phase: tEvents('types.' + (shipment.status as EventTypeValue)) }) }}
                    />
                    <button className="text-xs font-semibold text-orange-600 mt-2 hover:underline">{t('viewRecommendations')} &rarr;</button>
                </div>
            </div>
        </div>
    );
}

function ETADisplay({ eta, status }: { eta?: string | Date | null, status: string }) {
    const t = useTranslations('ShipmentDetails');
    if (!eta) return <span className="text-slate-400">-</span>;

    const daysLeft = Math.ceil((new Date(eta).getTime() - Date.now()) / (1000 * 60 * 60 * 24));

    if (status === EventType.FINAL_DELIVERY) {
        return <span className="text-emerald-600 font-bold">{t('delivered')}</span>;
    }

    if (daysLeft < 0) {
        return <span className="text-red-500 font-bold">{t('lateBy', { days: Math.abs(daysLeft) })}</span>;
    }

    return (
        <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold text-slate-700">{daysLeft}</span>
            <span className="text-xs text-slate-500 font-medium uppercase">{t('daysLeft')}</span>
        </div>
    );
}

function InfoItem({ label, value, icon, mono }: { label: string, value?: string | number | null, icon?: string, mono?: boolean }) {
    return (
        <div className="flex flex-col">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                {icon === 'user' && <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>}
                {icon === 'truck' && <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>}
                {icon === 'hashtag' && <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" /></svg>}
                {icon === 'box' && <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>}
                {icon === 'lock' && <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>}
                {label}
            </span>
            <span className={`text-sm font-semibold text-slate-700 ${mono ? 'font-mono' : ''}`}>
                {value || "-"}
            </span>
        </div>
    );
}

// Helper for labels removed - usage replaced by tEvents

export default function ShipmentDetailPage() {
    const { id } = useParams();
    const router = useRouter();
    const { token, canWrite, logout } = useAuth();
    const t = useTranslations('ShipmentDetails');
    const tEvents = useTranslations('Events');

    const [shipment, setShipment] = useState<Shipment | null>(null);
    const [events, setEvents] = useState<Event[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (token && id) fetchData();
    }, [token, id]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [sData, eData] = await Promise.all([
                shipmentService.getById(Number(id), token!),
                shipmentService.getEvents(Number(id), token!)
            ]);
            setShipment(sData);
            setEvents(eData);
        } catch (e) {
            console.error(e);
            // 401 Handled by AuthContext global listener
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="min-h-screen flex items-center justify-center text-slate-400">{t('loading')}</div>;
    if (!shipment) return <div className="p-10 text-center">{t('notFound')}</div>;

    return (
        <div className="max-w-7xl mx-auto space-y-6 pb-20 animate-fade-in">
            {/* Command Center Header */}
            <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
                    {/* Identity & Status */}
                    <div className="space-y-4 flex-1">
                        <div className="flex items-center gap-4">
                            <button onClick={() => router.back()} className="p-2 hover:bg-slate-100 rounded-full transition-colors -ml-2">
                                <svg className="w-5 h-5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
                            </button>
                            <div>
                                <div className="flex items-center gap-3">
                                    <h1 className="text-3xl font-bold text-brand-primary tracking-tight">{shipment.reference}</h1>
                                    <HealthBadge shipment={shipment} />
                                </div>
                                <div className="flex items-center gap-3 mt-1 text-sm text-slate-500">
                                    <span className="font-medium text-slate-700">{shipment.customer}</span>
                                    <span>•</span>
                                    <span className="bg-slate-100 px-2 py-0.5 rounded text-xs font-mono">{shipment.incoterm}</span>
                                    <span>•</span>
                                    <span className="flex items-center gap-1">
                                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                        {t('createdOn', { date: new Date(shipment.created_at).toLocaleDateString() })}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Quick Metrics Bar */}
                        <div className="flex items-center gap-8 pt-2">
                            <div>
                                <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">{t('currentStatus')}</div>
                                <Badge variant={getStatusVariant(shipment.status)} className="px-3 py-1 text-sm">
                                    {tEvents('types.' + (shipment.status as EventTypeValue)) || formatEventType(shipment.status)}
                                </Badge>
                                <span className="text-xs text-slate-400 ml-2 italic">
                                    {events[0] ? `${t('updated')} ${getTimeAgo(events[0].timestamp.toString(), t)}` : ''}
                                </span>
                            </div>
                            <div className="hidden md:block w-px h-10 bg-slate-100"></div>
                            <div className="hidden md:block">
                                <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">{t('estimatedDelay')}</div>
                                <ETADisplay eta={shipment.planned_eta} status={shipment.status} />
                            </div>
                        </div>
                    </div>

                    {/* Quick Actions Toolbar */}
                    <div className="flex flex-col gap-3 min-w-[200px]">
                        {canWrite && <AddEventModal shipmentId={shipment.id} onSuccess={fetchData} />}
                        <div className="grid grid-cols-2 gap-2">
                            <button className="flex items-center justify-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 hover:text-brand-secondary transition-colors group">
                                <svg className="w-4 h-4 text-slate-400 group-hover:text-brand-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                                {t('actions.email')}
                            </button>
                            <button className="flex items-center justify-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 hover:text-brand-secondary transition-colors group">
                                <svg className="w-4 h-4 text-slate-400 group-hover:text-brand-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                {t('actions.docs')}
                            </button>
                            <button className="flex items-center justify-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 hover:text-brand-secondary transition-colors group">
                                <svg className="w-4 h-4 text-slate-400 group-hover:text-brand-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" /></svg>
                                {t('actions.print')}
                            </button>
                            <button className="flex items-center justify-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-red-600 hover:bg-red-50 transition-colors border-red-100">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                                {t('actions.alert')}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Left Column: Data Cards */}
                <div className="lg:col-span-2 space-y-6">

                    <PredictiveInsight shipment={shipment} />

                    {/* Route & Dates - Enhanced */}
                    <Card className="animate-slide-up" style={{ animationDelay: '0.1s' }}>
                        <CardHeader title={t('routePlanning')}
                            action={<span className="text-xs text-slate-400 font-mono bg-slate-50 px-2 py-1 rounded border border-slate-100">M/V {shipment.vessel || "TBD"}</span>}
                        />
                        <div className="flex flex-col md:flex-row justify-between items-center gap-6 mt-6 relative pb-6 border-b border-surface-2">
                            {/* Progress Bar Background */}
                            <div className="absolute top-[18px] left-[10%] w-[80%] h-1 bg-slate-100 -z-10 hidden md:block rounded-full overflow-hidden">
                                <div className="h-full bg-slate-200 w-1/2"></div> {/* Mock progress */}
                            </div>

                            {/* Origin */}
                            <div className="flex flex-col items-center z-10 w-32 text-center">
                                <div className="w-10 h-10 rounded-full bg-white border-2 border-slate-200 flex items-center justify-center mb-3 shadow-sm">
                                    <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
                                </div>
                                <span className="text-sm font-bold text-slate-800">{shipment.origin?.split(',')[0]}</span>
                                <span className="text-xs text-slate-400 mt-1">ETD: {formatDate(shipment.planned_etd)}</span>
                            </div>

                            {/* Transit Badge */}
                            <div className="flex flex-col items-center z-10 bg-white px-2">
                                <div className="bg-slate-50 border border-slate-100 text-slate-500 text-[10px] font-bold px-2 py-1 rounded-full uppercase tracking-wider mb-2">
                                    {t('transit')}
                                </div>
                                <span className="text-xs font-mono text-slate-400">~25 j</span>
                            </div>

                            {/* Destination */}
                            <div className="flex flex-col items-center z-10 w-32 text-center">
                                <div className="w-10 h-10 rounded-full bg-white border-2 border-brand-primary flex items-center justify-center mb-3 shadow-md shadow-brand-primary/10">
                                    <svg className="w-5 h-5 text-brand-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                                </div>
                                <span className="text-sm font-bold text-brand-primary">{shipment.destination?.split(',')[0]}</span>
                                <span className="text-xs text-brand-secondary font-medium mt-1">ETA: {formatDate(shipment.planned_eta)}</span>
                            </div>
                        </div>

                        {/* MAD & ITS Dates Row */}
                        <div className="grid grid-cols-2 gap-4 mt-4 bg-slate-50 p-4 rounded-xl border border-slate-100">
                            {/* ... existing code ... */}
                            <div className="flex justify-between items-center">
                                <div>
                                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">{t('mad')}</span>
                                    <span className="text-sm font-bold text-slate-800">{shipment.mad_date ? new Date(shipment.mad_date).toLocaleDateString() : "-"}</span>
                                </div>
                            </div>
                            <div className="flex justify-between items-center border-l border-slate-200 pl-4">
                                <div>
                                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">{t('its')}</span>
                                    <span className="text-sm font-bold text-slate-800">{shipment.its_date ? new Date(shipment.its_date).toLocaleDateString() : "-"}</span>
                                </div>
                            </div>
                        </div>
                    </Card>

                    {/* Commercial Info - Enhanced Grid */}
                    <Card className="animate-slide-up" style={{ animationDelay: '0.2s' }}>
                        <CardHeader title={t('commercialInfo')} />
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-y-6 gap-x-4 mt-2">
                            <InfoItem label={t('customer')} value={shipment.customer} icon="user" />
                            <InfoItem label={t('supplier')} value={shipment.supplier} icon="truck" />
                            <InfoItem label={t('order')} value={shipment.order_number} icon="hashtag" />
                            <InfoItem label={t('sku')} value={shipment.sku} />
                            <InfoItem label={t('quantity')} value={shipment.quantity?.toLocaleString()} />
                            <InfoItem label={t('incoterm')} value={shipment.incoterm} />
                            <InfoItem label={t('place')} value={shipment.incoterm_city} />
                        </div>
                    </Card>

                    {/* Logistics Info */}
                    <Card className="animate-slide-up" style={{ animationDelay: '0.3s' }}>
                        <CardHeader title={t('logistics')} />
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-y-6 gap-x-4 mt-2">
                            <InfoItem label={t('container')} value={shipment.container_number} mono icon="box" />
                            <InfoItem label={t('seal')} value={shipment.seal_number} mono icon="lock" />
                            <InfoItem label={t('weight')} value={shipment.weight_kg ? `${shipment.weight_kg} kg` : '-'} />
                            <InfoItem label={t('volume')} value={shipment.volume_cbm ? `${shipment.volume_cbm} m³` : '-'} />
                            <InfoItem label={t('pallets')} value={shipment.nb_pallets?.toString()} />
                            <InfoItem label={t('cartons')} value={shipment.nb_cartons?.toString()} />
                        </div>
                    </Card>

                    {/* References - More Compact */}
                    <Card className="animate-slide-up" style={{ animationDelay: '0.4s' }}>
                        <CardHeader title={t('references')} />
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                            <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 flex justify-between items-start">
                                <div>
                                    <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">{t('pureTradeRef')}</div>
                                    <div className="font-mono text-sm font-bold text-slate-800">{shipment.pure_trade_ref || "-"}</div>
                                    <div className="text-xs text-slate-500 mt-2 flex items-center gap-1">
                                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                                        {shipment.responsable_pure_trade || t('unassigned')}
                                    </div>
                                </div>
                            </div>
                            <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 flex justify-between items-start">
                                <div>
                                    <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">{t('forwarderRef')}</div>
                                    <div className="font-mono text-sm font-bold text-slate-800">{shipment.forwarder_ref || "-"}</div>
                                    <div className="text-xs text-slate-500 mt-2 flex items-center gap-1">
                                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
                                        {shipment.interlocuteur || t('unassigned')}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Card>

                </div>


                {/* Right Column: Key Documents & Timeline */}
                <div className="lg:col-span-1 space-y-6">

                    {/* Quick Documents */}
                    <Card className="animate-slide-up" style={{ animationDelay: '0.4s' }}>
                        <CardHeader title={t('documents')} action={<button className="text-xs font-semibold text-brand-secondary hover:underline">{t('viewAll')}</button>} />
                        <div className="space-y-3 mt-4">
                            {[
                                { name: "Bill of Lading", type: "PDF", size: "2.4 MB", date: "24 Jan 2026" },
                                { name: "Packing List", type: "PDF", size: "1.1 MB", date: "22 Jan 2026" },
                                { name: "Commercial Invoice", type: "PDF", size: "854 KB", date: "22 Jan 2026" },
                            ].map((doc, i) => (
                                <div key={i} className="flex items-center justify-between p-3 bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors group cursor-pointer border border-slate-100">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded bg-white border border-slate-200 flex items-center justify-center text-red-500 shadow-sm">
                                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
                                        </div>
                                        <div>
                                            <div className="text-sm font-semibold text-slate-700 group-hover:text-brand-primary">{doc.name}</div>
                                            <div className="text-[10px] text-slate-400">{doc.date} • {doc.size}</div>
                                        </div>
                                    </div>
                                    <svg className="w-4 h-4 text-slate-300 group-hover:text-brand-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                                </div>
                            ))}
                            <button className="w-full py-2 border-2 border-dashed border-slate-200 rounded-lg text-sm text-slate-400 font-medium hover:border-brand-secondary hover:text-brand-secondary transition-colors flex items-center justify-center gap-2">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
                                {t('addDocument')}
                            </button>
                        </div>
                    </Card>

                    {/* Enhanced Timeline */}
                    <Card className="h-full max-h-[calc(100vh-100px)] overflow-y-auto animate-slide-up" style={{ animationDelay: '0.5s' }}>
                        <CardHeader title={t('activityLog')} action={<span className="text-xs font-mono bg-slate-100 px-2 py-0.5 rounded text-slate-500">{events.length} {t('logs')}</span>} />

                        <div className="relative border-l-2 border-slate-100 ml-4 mt-6 space-y-8 pb-4">
                            {events.map((event, idx) => {
                                const isLatest = idx === 0;
                                return (
                                    <div key={event.id} className="relative pl-8 group">
                                        {/* Dot with Pulse for latest */}
                                        <div className={`
                                            absolute -left-[9px] top-1.5 w-5 h-5 rounded-full border-4 border-white shadow-sm transition-all z-10 box-content
                                            ${isLatest ? 'bg-brand-primary ring-4 ring-brand-primary/10' : 'bg-slate-300 group-hover:bg-slate-400'}
                                        `}>
                                            {isLatest && <div className="absolute inset-0 rounded-full animate-ping bg-brand-primary opacity-20"></div>}
                                        </div>

                                        {/* Content */}
                                        <div className={`
                                            transition-all duration-300 relative
                                            ${isLatest ? 'opacity-100 translate-x-0' : 'opacity-70 group-hover:opacity-100'}
                                        `}>
                                            <div className="flex items-center justify-between">
                                                <div className="text-sm font-bold text-slate-800">
                                                    {tEvents('types.' + (event.type as EventTypeValue)) || formatEventType(event.type)}
                                                </div>
                                                <div className="text-[10px] font-mono text-slate-400 bg-slate-50 px-1.5 py-0.5 rounded">
                                                    {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                </div>
                                            </div>

                                            <div className="text-xs text-slate-500 mt-0.5 font-medium">
                                                {new Date(event.timestamp).toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' })}
                                            </div>

                                            {event.critical && (
                                                <div className="mt-2 inline-flex items-center gap-1.5 px-2 py-1 bg-red-50 border border-red-100 rounded text-xs font-semibold text-red-600">
                                                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                                                    {t('attentionRequired')}
                                                </div>
                                            )}

                                            {event.note && (
                                                <div className="mt-2 text-sm text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100 prose prose-sm max-w-none">
                                                    {event.note}
                                                </div>
                                            )}

                                            {/* Connector line enhancement */}
                                            {idx !== events.length - 1 && (
                                                <div className="absolute left-[-2rem] top-6 bottom-[-2rem] w-0.5 bg-slate-100 group-hover:bg-slate-200 transition-colors"></div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </Card>
                </div>

            </div>
        </div>
    );
}



