"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { shipmentService } from "@/services/shipmentService";
import { Shipment } from "@/types/shipment";
import ShipmentsTable from "@/components/ShipmentsTable";
import { Card } from "@/components/ui/Card";

interface Stats {
    total: number;
    inTransit: number;
    delivered: number;
    pending: number;
}

export default function DashboardPage() {
    const { canWrite, token, isLoading } = useAuth();
    const [stats, setStats] = useState<Stats>({ total: 0, inTransit: 0, delivered: 0, pending: 0 });
    const [loadingStats, setLoadingStats] = useState(true);

    useEffect(() => {
        if (token) {
            loadStats();
        }
    }, [token]);

    const loadStats = async () => {
        try {
            if (!token) return;
            const data = await shipmentService.getAll(token);

            const total = data.length;
            const delivered = data.filter((s) => s.status === "FINAL_DELIVERY").length;
            const inTransit = data.filter((s) => s.status && s.status.includes("TRANSIT")).length;
            const pending = total - delivered - inTransit;

            setStats({ total, inTransit, delivered, pending });
        } catch (e: any) {
            // Ignore 401 errors as they are handled globally
            if (e?.status !== 401) {
                console.error("Failed to load stats", e);
            }
        } finally {
            setLoadingStats(false);
        }
    };

    if (isLoading) return <div className="p-10 text-center animate-pulse text-slate-400">Chargement...</div>;

    return (
        <div className="space-y-10 animate-fade-in pb-20">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6 border-b border-slate-100 pb-6">
                <div>
                    <h1 className="text-3xl font-bold text-brand-primary tracking-tight">Vue d'ensemble</h1>
                    <p className="text-slate-500 mt-2 font-medium">Gérez vos expéditions et suivez vos performances.</p>
                </div>
                {canWrite && (
                    <Link href="/shipments/new" className="btn btn-primary shadow-lg shadow-brand-secondary/20 hover:shadow-brand-secondary/40 transition-all duration-300">
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        Nouvelle Expédition
                    </Link>
                )}
            </div>

            {/* Premium Stats Grid - Monochrome & Accents */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Total */}
                <div className="group relative bg-white p-6 rounded-2xl border border-slate-100 shadow-[0_4px_20px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.06)] transition-all duration-300">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Total Expéditions</p>
                            <h3 className="text-4xl font-bold text-brand-primary tracking-tight">{loadingStats ? "-" : stats.total}</h3>
                        </div>
                        <div className="p-2 bg-slate-50 rounded-lg group-hover:bg-slate-100 transition-colors">
                            <svg className="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                        </div>
                    </div>
                    <div className="mt-4 w-full bg-slate-100 h-1 rounded-full overflow-hidden">
                        <div className="bg-slate-800 h-full w-full opacity-10"></div>
                    </div>
                </div>

                {/* En Transit (Accent Rouge) */}
                <div className="group relative bg-white p-6 rounded-2xl border border-brand-secondary/10 shadow-[0_4px_20px_rgba(211,0,38,0.05)] hover:shadow-[0_8px_30px_rgba(211,0,38,0.1)] transition-all duration-300">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-xs font-semibold uppercase tracking-wider text-brand-secondary/80 mb-1">En Transit</p>
                            <h3 className="text-4xl font-bold text-brand-secondary tracking-tight">{loadingStats ? "-" : stats.inTransit}</h3>
                        </div>
                        <div className="p-2 bg-brand-secondary/5 rounded-lg group-hover:bg-brand-secondary/10 transition-colors">
                            <svg className="w-6 h-6 text-brand-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                    </div>
                    <div className="mt-4 w-full bg-slate-100 h-1 rounded-full overflow-hidden">
                        <div className="bg-brand-secondary h-full" style={{ width: `${stats.total ? (stats.inTransit / stats.total) * 100 : 0}%` }}></div>
                    </div>
                </div>

                {/* Livrées */}
                <div className="group relative bg-white p-6 rounded-2xl border border-slate-100 shadow-[0_4px_20px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.06)] transition-all duration-300">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Livrées</p>
                            <h3 className="text-4xl font-bold text-slate-700 tracking-tight">{loadingStats ? "-" : stats.delivered}</h3>
                        </div>
                        <div className="p-2 bg-slate-50 rounded-lg group-hover:bg-green-50/50 transition-colors">
                            <svg className="w-6 h-6 text-slate-400 group-hover:text-green-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 13l4 4L19 7" />
                            </svg>
                        </div>
                    </div>
                    <div className="mt-4 w-full bg-slate-100 h-1 rounded-full overflow-hidden">
                        <div className="bg-slate-400 h-full" style={{ width: `${stats.total ? (stats.delivered / stats.total) * 100 : 0}%` }}></div>
                    </div>
                </div>

                {/* En Attente */}
                <div className="group relative bg-white p-6 rounded-2xl border border-slate-100 shadow-[0_4px_20px_rgba(0,0,0,0.03)] hover:shadow-[0_8px_30px_rgba(0,0,0,0.06)] transition-all duration-300">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">En Attente</p>
                            <h3 className="text-4xl font-bold text-slate-700 tracking-tight">{loadingStats ? "-" : stats.pending}</h3>
                        </div>
                        <div className="p-2 bg-slate-50 rounded-lg group-hover:bg-amber-50/50 transition-colors">
                            <svg className="w-6 h-6 text-slate-400 group-hover:text-amber-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                    </div>
                    <div className="mt-4 w-full bg-slate-100 h-1 rounded-full overflow-hidden">
                        <div className="bg-slate-300 h-full" style={{ width: `${stats.total ? (stats.pending / stats.total) * 100 : 0}%` }}></div>
                    </div>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="space-y-6">
                <div className="flex items-center justify-between px-1">
                    <h2 className="text-xl font-bold text-brand-primary flex items-center gap-3">
                        <span className="w-1.5 h-6 bg-brand-secondary rounded-full inline-block"></span>
                        Expéditions Récentes
                    </h2>
                    <Link href="/shipments" className="group flex items-center text-sm font-semibold text-slate-500 hover:text-brand-secondary transition-colors">
                        Voir tout l'historique
                        <svg className="w-4 h-4 ml-1 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                        </svg>
                    </Link>
                </div>

                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                    <ShipmentsTable />
                </div>
            </div>
        </div>
    );
}

