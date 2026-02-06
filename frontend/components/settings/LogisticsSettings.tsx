"use client";

import { useState, useEffect } from "react";
import { apiFetch } from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";

export default function LogisticsSettings() {
    const { token } = useAuth();
    const [isLoading, setIsLoading] = useState(false);
    const [config, setConfig] = useState({
        cmaClientId: "",
        cmaClientSecret: "",
        maerskClientId: "",
        maerskClientSecret: "",
        vesselFinderKey: "",
        usitcToken: ""
    });

    useEffect(() => {
        const loadConfig = async () => {
            if (!token) return;
            try {
                const data = await apiFetch<Record<string, string>>('/settings/', { token });
                setConfig({
                    cmaClientId: data['CMA_CLIENT_ID'] || "",
                    cmaClientSecret: data['CMA_CLIENT_SECRET'] || "",
                    maerskClientId: data['MAERSK_CLIENT_ID'] || "",
                    maerskClientSecret: data['MAERSK_CLIENT_SECRET'] || "",
                    vesselFinderKey: data['VESSELFINDER_KEY'] || "",
                    usitcToken: data['USITC_TOKEN'] || ""
                });
            } catch (e) {
                console.error("Failed to load logistics settings", e);
            }
        };

        loadConfig();
    }, [token]);

    const saveConfig = async () => {
        if (!token) return;
        setIsLoading(true);
        try {
            await apiFetch('/settings/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify([
                    { key: 'CMA_CLIENT_ID', value: config.cmaClientId },
                    { key: 'CMA_CLIENT_SECRET', value: config.cmaClientSecret, is_encrypted: true },
                    { key: 'MAERSK_CLIENT_ID', value: config.maerskClientId },
                    { key: 'MAERSK_CLIENT_SECRET', value: config.maerskClientSecret, is_encrypted: true },
                    { key: 'VESSELFINDER_KEY', value: config.vesselFinderKey, is_encrypted: true },
                    { key: 'USITC_TOKEN', value: config.usitcToken, is_encrypted: true }
                ]),
                token
            });
            alert("Configuration sauvegardée avec succès !");
        } catch (e) {
            console.error(e);
            alert("Erreur lors de la sauvegarde");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
                <div className="mb-6">
                    <h3 className="text-lg font-semibold text-slate-800">APIs Logistiques & Transporteurs</h3>
                    <p className="text-sm text-slate-500 mt-1">Configurez les accès aux services externes pour la synchronisation automatique.</p>
                </div>

                <div className="space-y-8">
                    {/* CMA CGM Section */}
                    <div className="p-5 bg-slate-50 rounded-lg border border-slate-200">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="h-8 w-8 bg-blue-900 rounded flex items-center justify-center text-white text-xs font-bold">CMA</div>
                            <h4 className="font-semibold text-slate-800">CMA CGM Group</h4>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs font-medium text-slate-500 mb-1">Client ID</label>
                                <input
                                    type="text"
                                    value={config.cmaClientId}
                                    onChange={(e) => setConfig({ ...config, cmaClientId: e.target.value })}
                                    className="w-full text-sm rounded border-slate-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                                    placeholder="Ex: id-1234..."
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-slate-500 mb-1">Client Secret</label>
                                <input
                                    type="password"
                                    value={config.cmaClientSecret}
                                    onChange={(e) => setConfig({ ...config, cmaClientSecret: e.target.value })}
                                    className="w-full text-sm rounded border-slate-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                                    placeholder="••••••••••••••••"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Maersk Section */}
                    <div className="p-5 bg-slate-50 rounded-lg border border-slate-200">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="h-8 w-8 bg-[#42B3E5] rounded flex items-center justify-center text-white text-xs font-bold">★</div>
                            <h4 className="font-semibold text-slate-800">Maersk</h4>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs font-medium text-slate-500 mb-1">Consumer Key (Client ID)</label>
                                <input
                                    type="text"
                                    value={config.maerskClientId}
                                    onChange={(e) => setConfig({ ...config, maerskClientId: e.target.value })}
                                    className="w-full text-sm rounded border-slate-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                                    placeholder="Ex: AkJ8..."
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-slate-500 mb-1">Consumer Secret</label>
                                <input
                                    type="password"
                                    value={config.maerskClientSecret}
                                    onChange={(e) => setConfig({ ...config, maerskClientSecret: e.target.value })}
                                    className="w-full text-sm rounded border-slate-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                                    placeholder="••••••••••••••••"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Tracking & Data Services */}
                    <div className="p-5 bg-slate-50 rounded-lg border border-slate-200">
                        <div className="flex items-center gap-3 mb-4">
                            <h4 className="font-semibold text-slate-800">Services de Données</h4>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs font-medium text-slate-500 mb-1">VesselFinder API Key</label>
                                <input
                                    type="password"
                                    value={config.vesselFinderKey}
                                    onChange={(e) => setConfig({ ...config, vesselFinderKey: e.target.value })}
                                    className="w-full text-sm rounded border-slate-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                                    placeholder="Clé API VesselFinder"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-slate-500 mb-1">USITC DataWeb Token (Login.gov)</label>
                                <input
                                    type="password"
                                    value={config.usitcToken}
                                    onChange={(e) => setConfig({ ...config, usitcToken: e.target.value })}
                                    className="w-full text-sm rounded border-slate-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                                    placeholder="Bearer Token"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-end pt-4 border-t border-slate-100">
                        <button
                            onClick={saveConfig}
                            disabled={isLoading}
                            className="bg-brand-primary hover:bg-brand-dark text-white px-6 py-2.5 rounded-lg font-medium transition-all shadow-sm flex items-center gap-2"
                        >
                            {isLoading ? (
                                <span className="animate-spin h-4 w-4 border-2 border-white/30 border-t-white rounded-full"></span>
                            ) : (
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            )}
                            Sauvegarder les configurations
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
