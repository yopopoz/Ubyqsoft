"use client";

import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/services/api";
import { useSearchParams, useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function CloudSettings() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const { token } = useAuth();
    const [isConnected, setIsConnected] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [config, setConfig] = useState({
        clientId: "",
        clientSecret: "",
        tenantId: "common"
    });
    const [showConfig, setShowConfig] = useState(false);

    useEffect(() => {
        const checkStatus = async () => {
            if (!token) return;
            try {
                const data = await apiFetch<Record<string, any>>('/settings/', { token });
                if (data['MS_ACCESS_TOKEN']) {
                    setIsConnected(true);
                }
                setConfig({
                    clientId: data['MS_CLIENT_ID'] || "",
                    clientSecret: data['MS_CLIENT_SECRET'] || "",
                    tenantId: data['MS_TENANT_ID'] || "common"
                });

                // Show config if no keys
                if (!data['MS_CLIENT_ID']) {
                    setShowConfig(true);
                }
            } catch (e) {
                console.error(e);
            }
        };

        if (token) checkStatus();
        if (searchParams.get('success') === 'true') {
            setIsConnected(true);
            // Clear params
            router.replace('/admin/settings?tab=cloud');
        }
    }, [token, searchParams, router]);

    // checkStatus definition removed (moved inside useEffect)

    const saveConfig = async () => {
        try {
            await apiFetch('/settings/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify([
                    { key: 'MS_CLIENT_ID', value: config.clientId },
                    { key: 'MS_CLIENT_SECRET', value: config.clientSecret, is_encrypted: true },
                    { key: 'MS_TENANT_ID', value: config.tenantId }
                ]),
                token
            });
            return true;
        } catch (e) {
            alert("Erreur de sauvegarde");
            return false;
        }
    };

    const handleConnect = async () => {
        if (!config.clientId || !config.clientSecret) {
            alert("Veuillez d'abord configurer le Client ID et le Secret.");
            setShowConfig(true);
            return;
        }

        setIsLoading(true);
        try {
            // First save config
            const saved = await saveConfig();
            if (!saved) return;

            // Then get auth url
            const res = await apiFetch<{ url: string }>('/auth/microsoft/login', { token });
            // Redirect to Microsoft
            window.location.href = res.url;
        } catch (e) {
            console.error(e);
            alert("Erreur lors de l'initialisation de la connexion");
            setIsLoading(false);
        }
    };

    const handleDisconnect = async () => {
        if (confirm("Êtes-vous sûr de vouloir déconnecter le compte Microsoft ?")) {
            try {
                // Remove tokens
                await apiFetch('/settings/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify([
                        { key: 'MS_ACCESS_TOKEN', value: "" },
                        { key: 'MS_REFRESH_TOKEN', value: "" }
                    ]),
                    token
                });
                setIsConnected(false);
            } catch (e) {
                alert("Erreur lors de la déconnexion");
            }
        }
    };

    return (
        <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h3 className="text-lg font-semibold text-slate-800">Microsoft Cloud</h3>
                        <p className="text-sm text-slate-500 mt-1">Gérez la connexion avec vos services Azure et Office 365</p>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${isConnected ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-600"
                        }`}>
                        {isConnected ? "Connecté" : "Déconnecté"}
                    </div>
                </div>

                {/* Configuration Section */}
                <div className="mb-8 p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="flex justify-between items-center mb-4 cursor-pointer" onClick={() => setShowConfig(!showConfig)}>
                        <h4 className="text-sm font-semibold text-slate-700">Configuration Azure AD App</h4>
                        <span className="text-xs text-blue-600 hover:text-blue-800">
                            {showConfig ? 'Masquer' : 'Modifier les clés'}
                        </span>
                    </div>

                    {showConfig && (
                        <div className="grid grid-cols-1 gap-4 animate-fadeIn">
                            <div>
                                <label className="block text-xs font-medium text-slate-500 mb-1">Application (Client) ID</label>
                                <input
                                    type="text"
                                    value={config.clientId}
                                    onChange={(e) => setConfig({ ...config, clientId: e.target.value })}
                                    className="w-full text-sm rounded border-slate-300"
                                    placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-slate-500 mb-1">Client Secret</label>
                                <input
                                    type="password"
                                    value={config.clientSecret}
                                    onChange={(e) => setConfig({ ...config, clientSecret: e.target.value })}
                                    className="w-full text-sm rounded border-slate-300"
                                    placeholder="Client Secret Value"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-slate-500 mb-1">Directory (Tenant) ID</label>
                                <input
                                    type="text"
                                    value={config.tenantId}
                                    onChange={(e) => setConfig({ ...config, tenantId: e.target.value })}
                                    className="w-full text-sm rounded border-slate-300"
                                    placeholder="common"
                                />
                            </div>
                        </div>
                    )}
                </div>

                <div className="flex items-center gap-4">
                    {!isConnected ? (
                        <button
                            onClick={handleConnect}
                            disabled={isLoading}
                            className="bg-[#0078D4] hover:bg-[#006cbd] text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
                        >
                            {isLoading ? (
                                <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                            ) : (
                                <svg className="h-5 w-5" viewBox="0 0 23 23" fill="currentColor">
                                    <path d="M0 0h11v11H0zM12 0h11v11H12zM0 12h11v11H0zM12 12h11v11H12z" />
                                </svg>
                            )}
                            Se connecter avec Microsoft
                        </button>
                    ) : (
                        <div className="flex items-center justify-between w-full bg-slate-50 p-4 rounded-lg border border-slate-200">
                            <div className="flex items-center gap-3">
                                <div className="h-10 w-10 bg-[#0078D4] text-white flex items-center justify-center rounded-lg">
                                    <svg className="h-6 w-6" viewBox="0 0 23 23" fill="currentColor">
                                        <path d="M0 0h11v11H0zM12 0h11v11H12zM0 12h11v11H0zM12 12h11v11H12z" />
                                    </svg>
                                </div>
                                <div>
                                    <p className="font-medium text-slate-900">Compte Connecté</p>
                                    <p className="text-sm text-slate-500">Autorisations actives</p>
                                </div>
                            </div>
                            <button
                                onClick={handleDisconnect}
                                className="text-red-600 hover:text-red-700 font-medium text-sm px-3 py-2 hover:bg-red-50 rounded-lg transition-colors"
                            >
                                Déconnecter
                            </button>
                        </div>
                    )}
                </div>

                {/* OneDrive Sync Configuration */}
                {isConnected && <OneDriveSyncConfig token={token} />}

                <div className="mt-8 border-t border-slate-100 pt-6">
                    <h4 className="text-sm font-semibold text-slate-800 mb-4">Permissions requises</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {['Outlook Mail', 'Calendar', 'OneDrive', 'SharePoint', 'Teams'].map((scope) => (
                            <div key={scope} className="flex items-start gap-3 p-3 rounded-lg border border-slate-100">
                                <div className={`h-2 w-2 mt-2 rounded-full ${isConnected ? "bg-green-500" : "bg-slate-300"}`} />
                                <div>
                                    <p className="text-sm font-medium text-slate-700">{scope}</p>
                                    <p className="text-xs text-slate-500">Lecture et écriture</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

function OneDriveSyncConfig({ token }: { token: string | null }) {
    const [isRealtime, setIsRealtime] = useState(false);
    const [subInfo, setSubInfo] = useState<{ id: string, expirationDateTime: string } | null>(null);
    const [config, setConfig] = useState<Record<string, any>>({});
    const [files, setFiles] = useState<any[]>([]);
    const [isLoadingFiles, setIsLoadingFiles] = useState(false);
    const [isSelecting, setIsSelecting] = useState(false);
    const [isSyncing, setIsSyncing] = useState(false);

    const loadConfig = useCallback(async () => {
        try {
            const data = await apiFetch<Record<string, any>>('/sync/onedrive/config', { token });
            setConfig(data);
        } catch (e) {
            console.error(e);
        }
    }, [token]);

    const loadSubscription = useCallback(async () => {
        try {
            const data = await apiFetch<Record<string, any>>('/sync/onedrive/subscription', { token });
            if (data && data.id) {
                setIsRealtime(true);
                setSubInfo(data as any);
            } else {
                setIsRealtime(false);
                setSubInfo(null);
            }
        } catch (e) {
            console.error(e);
        }
    }, [token]);

    useEffect(() => {
        loadConfig();
        loadSubscription();
    }, [loadConfig, loadSubscription]);

    // loadSubscription removal (handled above)

    const toggleRealtime = async () => {
        const newState = !isRealtime;
        try {
            await apiFetch(`/sync/onedrive/subscribe?enable=${newState}`, {
                method: 'POST',
                token
            });
            setIsRealtime(newState);
            loadSubscription();
            if (newState) alert("Mode temps réel activé !");
            else alert("Mode temps réel désactivé.");
        } catch (e) {
            alert("Erreur lors du changement de mode");
        }
    };

    // loadConfig removal (handled above)

    const loadFiles = async () => {
        setIsLoadingFiles(true);
        try {
            const data = await apiFetch<any[]>('/sync/onedrive/files', { token });
            setFiles(data);
            setIsSelecting(true);
        } catch (e) {
            alert("Erreur chargement fichiers OneDrive");
        } finally {
            setIsLoadingFiles(false);
        }
    };

    const selectFile = async (file: any) => {
        try {
            await apiFetch('/sync/onedrive/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_id: file.id, file_name: file.name }),
                token
            });
            setConfig({ ...config, file_id: file.id, file_name: file.name });
            setIsSelecting(false);
            alert("Fichier maître configuré !");
        } catch (e) {
            alert("Erreur sauvegarde config");
        }
    };

    const runSync = async () => {
        setIsSyncing(true);
        try {
            const res = await apiFetch<any>('/sync/onedrive/run', {
                method: 'POST',
                token
            });
            alert(`Synchro terminée !\nCréés: ${res.created}\nMis à jour: ${res.updated}\nIgnorés: ${res.skipped}\nErreurs: ${res.errors.length}`);
            loadConfig(); // Reload last_run
        } catch (e) {
            alert("Erreur lors de la synchronisation");
        } finally {
            setIsSyncing(false);
        }
    };

    return (
        <div className="mt-8 pt-6 border-t border-slate-100">
            <h4 className="text-lg font-semibold text-slate-800 mb-4">Synchronisation OneDrive</h4>

            {config.file_id ? (
                <div className="bg-slate-50 rounded-lg border border-slate-200 p-4">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-sm font-medium text-slate-500">Fichier Maître</p>
                            <div className="flex items-center gap-2 mt-1">
                                <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                    <polyline points="14 2 14 8 20 8"></polyline>
                                </svg>
                                <span className="font-semibold text-slate-800">{config.file_name}</span>
                            </div>
                            {config.last_run && (
                                <p className="text-xs text-slate-400 mt-2">
                                    Dernière synchro : {new Date(config.last_run).toLocaleString()}
                                </p>
                            )}

                            {/* Realtime Toggle */}
                            <div className="mt-4 flex items-center gap-3">
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input type="checkbox" className="sr-only peer" checked={isRealtime} onChange={toggleRealtime} />
                                    <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                    <span className="ml-3 text-sm font-medium text-slate-700">Mode Temps Réel</span>
                                </label>
                                {isRealtime && subInfo?.expirationDateTime && (
                                    <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded border border-green-100">
                                        Actif (Expire: {new Date(subInfo.expirationDateTime).toLocaleDateString()})
                                    </span>
                                )}
                            </div>

                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={loadFiles}
                                className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-200 rounded-lg transition-colors"
                                title="Changer de fichier"
                            >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                </svg>
                            </button>
                            <button
                                onClick={runSync}
                                disabled={isSyncing}
                                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                            >
                                {isSyncing ? (
                                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                ) : (
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                    </svg>
                                )}
                                Synchroniser
                            </button>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="text-center p-8 bg-slate-50 rounded-lg border border-dashed border-slate-300">
                    <div className="inline-flex p-3 rounded-full bg-slate-100 mb-4">
                        <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                        </svg>
                    </div>
                    <h5 className="text-sm font-medium text-slate-900">Aucun fichier configuré</h5>
                    <p className="text-sm text-slate-500 mb-4">Sélectionnez un fichier Excel sur votre OneDrive pour activer la synchronisation.</p>
                    <button
                        onClick={loadFiles}
                        disabled={isLoadingFiles}
                        className="px-4 py-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg font-medium transition-colors inlin-flex items-center gap-2"
                    >
                        {isLoadingFiles ? "Chargement..." : "Sélectionner un fichier"}
                    </button>
                </div>
            )}

            {/* File Selector Modal / List */}
            {isSelecting && (
                <div className="mt-4 border rounded-lg overflow-hidden border-slate-200 animate-fadeIn">
                    <div className="bg-slate-50 px-4 py-2 border-b border-slate-200 flex justify-between items-center">
                        <span className="font-medium text-sm text-slate-700">Fichiers Excel récents</span>
                        <button onClick={() => setIsSelecting(false)} className="text-slate-400 hover:text-slate-600">×</button>
                    </div>
                    <div className="max-h-60 overflow-y-auto">
                        {files.length === 0 ? (
                            <div className="p-4 text-center text-sm text-slate-500">Aucun fichier .xlsx trouvé</div>
                        ) : (
                            files.map((f) => (
                                <div
                                    key={f.id}
                                    onClick={() => selectFile(f)}
                                    className="p-3 hover:bg-blue-50 cursor-pointer flex items-center justify-between border-b border-slate-100 last:border-0"
                                >
                                    <div className="flex items-center gap-3">
                                        <svg className="w-5 h-5 text-green-600 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                        </svg>
                                        <div>
                                            <p className="text-sm font-medium text-slate-800">{f.name}</p>
                                            <p className="text-xs text-slate-500">{f.path}</p>
                                        </div>
                                    </div>
                                    <span className="text-xs text-slate-400">
                                        {new Date(f.lastModified).toLocaleDateString()}
                                    </span>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

