"use client";

import { useState, useEffect, useCallback } from "react";
import { useTranslations } from "next-intl";
import { useAuth } from "@/contexts/AuthContext";
import { apiFetch } from "@/services/api";
import { format } from "date-fns";
import { fr } from "date-fns/locale";

interface ApiKey {
    id: number;
    name: string;
    prefix: string;
    created_at: string;
    last_used_at: string | null;
    is_active: boolean;
}

interface ApiKeyCreated extends ApiKey {
    key: string;
}

export default function SecuritySettings() {
    const t = useTranslations("Settings.Security");
    const { token } = useAuth();
    const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newKeyName, setNewKeyName] = useState("");
    const [createdKey, setCreatedKey] = useState<string | null>(null);

    const fetchKeys = useCallback(async () => {
        if (!token) return;
        setIsLoading(true);
        try {
            const data = await apiFetch<ApiKey[]>("/settings/api-keys/", { token });
            setApiKeys(data);
        } catch (e) {
            console.error(e);
        } finally {
            setIsLoading(false);
        }
    }, [token]);

    useEffect(() => {
        fetchKeys();
    }, [fetchKeys]);

    const handleCreateKey = async () => {
        if (!newKeyName.trim()) return;
        try {
            const data = await apiFetch<ApiKeyCreated>("/settings/api-keys/", {
                token,
                method: "POST",
                body: JSON.stringify({ name: newKeyName })
            });
            setCreatedKey(data.key); // Provide the full key to user
            setNewKeyName("");
            fetchKeys(); // Refresh list
        } catch (e) {
            console.error(e);
            alert("Erreur lors de la création de la clé");
        }
    };

    const handleRevoke = async (id: number) => {
        if (!confirm("Voulez-vous vraiment révoquer cette clé ? Cette action est irréversible.")) return;
        try {
            await apiFetch(`/settings/api-keys/${id}`, {
                token,
                method: "DELETE"
            });
            fetchKeys();
        } catch (e) {
            console.error(e);
            alert("Erreur lors de la révocation");
        }
    };

    const closeCreateModal = () => {
        setShowCreateModal(false);
        setCreatedKey(null);
        setNewKeyName("");
    }

    return (
        <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h3 className="text-lg font-semibold text-slate-800">{t("title")}</h3>
                        <p className="text-sm text-slate-500">{t("description")}</p>
                    </div>
                    <button
                        onClick={() => setShowCreateModal(true)}
                        className="bg-brand-primary hover:bg-brand-secondary text-white px-4 py-2 rounded-lg font-medium transition-colors"
                    >
                        {t("generate")}
                    </button>
                </div>

                {isLoading ? (
                    <div className="text-center py-8 text-slate-500">Chargement...</div>
                ) : (
                    <div className="space-y-4">
                        {apiKeys.length === 0 && (
                            <div className="text-center py-8 text-slate-400 italic">Aucune clé API active.</div>
                        )}
                        {apiKeys.map((key) => (
                            <div key={key.id} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
                                <div>
                                    <h4 className="font-medium text-slate-900">{key.name}</h4>
                                    <div className="flex items-center gap-4 mt-1">
                                        <code className="bg-white px-2 py-0.5 rounded border border-slate-200 text-xs font-mono text-slate-600">
                                            {key.prefix}****************
                                        </code>
                                        <span className="text-xs text-slate-500">
                                            {t("created", { date: format(new Date(key.created_at), "dd MMM yyyy", { locale: fr }) })}
                                        </span>
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <span className="text-xs text-slate-500">
                                        {key.last_used_at
                                            ? `Dernier usage : ${format(new Date(key.last_used_at), "dd MMM HH:mm", { locale: fr })}`
                                            : "Jamais utilisée"}
                                    </span>
                                    <button
                                        onClick={() => handleRevoke(key.id)}
                                        className="text-red-600 hover:text-red-700 text-sm font-medium"
                                    >
                                        {t("revoke")}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Create / Success Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden">
                        <div className="p-6">
                            <h3 className="text-lg font-semibold text-slate-900 mb-4">
                                {createdKey ? "Clé API Créée" : "Nouvelle Clé API"}
                            </h3>

                            {createdKey ? (
                                <div className="space-y-4">
                                    <div className="bg-amber-50 border border-amber-200 text-amber-800 p-3 rounded-lg text-sm">
                                        Cette clé ne sera affichée qu&apos;une seule fois. Veuillez la copier maintenant.
                                    </div>

                                    <div className="relative">
                                        <pre className="bg-slate-900 text-slate-50 p-4 rounded-lg text-sm font-mono break-all whitespace-pre-wrap">
                                            {createdKey}
                                        </pre>
                                        <button
                                            onClick={() => navigator.clipboard.writeText(createdKey)}
                                            className="absolute top-2 right-2 text-xs bg-white/10 hover:bg-white/20 text-white px-2 py-1 rounded transition-colors"
                                        >
                                            Copier
                                        </button>
                                    </div>

                                    <div className="flex justify-end pt-2">
                                        <button
                                            onClick={closeCreateModal}
                                            className="bg-brand-primary hover:bg-brand-secondary text-white px-4 py-2 rounded-lg font-medium transition-colors"
                                        >
                                            J&apos;ai copié la clé
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Nom de la clé</label>
                                        <input
                                            type="text"
                                            value={newKeyName}
                                            onChange={(e) => setNewKeyName(e.target.value)}
                                            placeholder="ex: Intégration Zapier"
                                            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-primary/20"
                                            autoFocus
                                        />
                                    </div>
                                    <div className="flex justify-end gap-3 pt-4">
                                        <button
                                            onClick={() => setShowCreateModal(false)}
                                            className="text-slate-600 hover:text-slate-800 px-4 py-2"
                                        >
                                            Annuler
                                        </button>
                                        <button
                                            onClick={handleCreateKey}
                                            disabled={!newKeyName.trim()}
                                            className="bg-brand-primary disabled:opacity-50 text-white px-4 py-2 rounded-lg"
                                        >
                                            Générer
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
