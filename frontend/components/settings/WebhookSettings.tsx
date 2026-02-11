"use client";

import { useState, useEffect, useCallback } from "react";
import { useTranslations } from "next-intl";
import { useAuth } from "@/contexts/AuthContext";
import { apiFetch } from "@/services/api";

interface Webhook {
    id: number;
    url: string;
    events: string[];
    isActive: boolean;
    lastTriggered?: string;
    secret?: string;
}

interface BackendWebhook {
    id: number;
    url: string;
    events: string[];
    is_active: boolean;
    last_triggered_at?: string;
    secret?: string;
}

export default function WebhookSettings() {
    const t = useTranslations('Settings.Webhooks');
    const { token } = useAuth();
    const [webhooks, setWebhooks] = useState<Webhook[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);

    // Form State
    const [newUrl, setNewUrl] = useState("");
    const [selectedEvents, setSelectedEvents] = useState<string[]>([]);

    const availableEvents = [
        "shipment.created",
        "event.created",
        "alert.created"
    ];

    const fetchWebhooks = useCallback(async () => {
        if (!token) return;
        setIsLoading(true);
        try {
            const data = await apiFetch<BackendWebhook[]>('/settings/webhooks/', { token });
            // Map backend naming to frontend naming if needed (snake_case vs camelCase)
            // But our Pydantic model uses `orm_mode=True` which matches DB columns.
            // DB has `is_active`, we used `isActive` in TS interface.
            // Let's adjust the interface or the mapping.
            // Actually, let's fix the interface to match Pydantic response (is_active).
            setWebhooks(data.map((w) => ({
                ...w,
                isActive: w.is_active,
                lastTriggered: w.last_triggered_at
            })));
        } catch {
            alert("Erreur lors du chargement des webhooks");
        } finally {
            setIsLoading(false);
        }
    }, [token]);

    useEffect(() => {
        fetchWebhooks();
    }, [fetchWebhooks]);

    const handleCreate = async () => {
        if (!newUrl) return alert("URL requise");
        if (selectedEvents.length === 0) return alert("Sélectionnez au moins un événement");

        try {
            await apiFetch('/settings/webhooks/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: newUrl,
                    events: selectedEvents,
                    is_active: true
                }),
                token
            });
            setIsModalOpen(false);
            setNewUrl("");
            setSelectedEvents([]);
            fetchWebhooks();
        } catch {
            alert("Erreur lors de la création");
        }
    };

    const toggleWebhook = async (id: number, currentStatus: boolean) => {
        try {
            await apiFetch(`/settings/webhooks/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: !currentStatus }),
                token
            });
            setWebhooks(hooks => hooks.map(h =>
                h.id === id ? { ...h, isActive: !h.isActive } : h
            ));
        } catch {
            alert("Erreur de mise à jour");
        }
    };

    const deleteWebhook = async (id: number) => {
        if (!confirm(t('table.confirmDelete'))) return;
        try {
            await apiFetch(`/settings/webhooks/${id}`, {
                method: 'DELETE',
                token
            });
            setWebhooks(hooks => hooks.filter(h => h.id !== id));
        } catch {
            alert("Erreur de suppression");
        }
    };

    const toggleEventSelection = (event: string) => {
        if (selectedEvents.includes(event)) {
            setSelectedEvents(prev => prev.filter(e => e !== event));
        } else {
            setSelectedEvents(prev => [...prev, event]);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                <div>
                    <h3 className="text-lg font-semibold text-slate-800">{t('title')}</h3>
                    <p className="text-sm text-slate-500">{t('description')}</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="bg-brand-primary hover:bg-brand-secondary text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    {t('new')}
                </button>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                <table className="min-w-full divide-y divide-slate-200">
                    <thead className="bg-slate-50">
                        <tr>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">{t('table.endpoint')}</th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">{t('table.events')}</th>
                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">{t('table.status')}</th>
                            <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">{t('table.actions')}</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-200">
                        {isLoading ? (
                            <tr>
                                <td colSpan={4} className="px-6 py-4 text-center text-sm text-slate-500">Chargement...</td>
                            </tr>
                        ) : webhooks.length === 0 ? (
                            <tr>
                                <td colSpan={4} className="px-6 py-4 text-center text-sm text-slate-500">Aucun webhook configuré.</td>
                            </tr>
                        ) : (
                            webhooks.map((hook) => (
                                <tr key={hook.id}>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-slate-900">{hook.url}</div>
                                        <div className="text-xs text-slate-500">Dernier appel: {hook.lastTriggered ? new Date(hook.lastTriggered).toLocaleString() : t('table.never')}</div>
                                        {hook.secret && <div className="text-xs text-slate-400 font-mono mt-1" title="Secret HMAC">Secret: {hook.secret.substring(0, 8)}...</div>}
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex flex-wrap gap-2">
                                            {hook.events.map(event => (
                                                <span key={event} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                                    {event}
                                                </span>
                                            ))}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <button
                                            onClick={() => toggleWebhook(hook.id, hook.isActive)}
                                            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${hook.isActive ? 'bg-green-500' : 'bg-slate-200'}`}
                                        >
                                            <span className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${hook.isActive ? 'translate-x-5' : 'translate-x-0'}`} />
                                        </button>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button
                                            onClick={() => deleteWebhook(hook.id)}
                                            className="text-red-600 hover:text-red-900 transition-colors"
                                        >
                                            {t('table.delete')}
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Create Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
                        <h3 className="text-lg font-semibold text-slate-800 mb-4">{t('new')}</h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">URL du Endpoint</label>
                                <input
                                    type="url"
                                    value={newUrl}
                                    onChange={(e) => setNewUrl(e.target.value)}
                                    className="w-full rounded-lg border-slate-300 focus:ring-brand-primary focus:border-brand-primary"
                                    placeholder="https://api.monsite.com/webhook"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">Événements</label>
                                <div className="space-y-2">
                                    {availableEvents.map(event => (
                                        <label key={event} className="flex items-center gap-2 cursor-pointer">
                                            <input
                                                type="checkbox"
                                                checked={selectedEvents.includes(event)}
                                                onChange={() => toggleEventSelection(event)}
                                                className="rounded border-slate-300 text-brand-primary focus:ring-brand-primary"
                                            />
                                            <span className="text-sm text-slate-600 font-mono bg-slate-100 px-2 py-0.5 rounded">{event}</span>
                                        </label>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className="mt-6 flex justify-end gap-3">
                            <button
                                onClick={() => setIsModalOpen(false)}
                                className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                            >
                                Annuler
                            </button>
                            <button
                                onClick={handleCreate}
                                className="px-4 py-2 bg-brand-primary text-white hover:bg-brand-secondary rounded-lg transition-colors"
                            >
                                Créer
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
