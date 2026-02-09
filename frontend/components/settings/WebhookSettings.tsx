"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

interface Webhook {
    id: string;
    url: string;
    events: string[];
    isActive: boolean;
    lastTriggered?: string;
}

export default function WebhookSettings() {
    const t = useTranslations('Settings.Webhooks');
    const [webhooks, setWebhooks] = useState<Webhook[]>([
        {
            id: '1',
            url: 'https://api.example.com/hooks/shipments',
            events: ['shipment.created', 'shipment.updated'],
            isActive: true,
            lastTriggered: '2024-01-26 14:30:00'
        }
    ]);

    const toggleWebhook = (id: string) => {
        setWebhooks(hooks => hooks.map(h =>
            h.id === id ? { ...h, isActive: !h.isActive } : h
        ));
    };

    const deleteWebhook = (id: string) => {
        if (confirm(t('table.confirmDelete'))) {
            setWebhooks(hooks => hooks.filter(h => h.id !== id));
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                <div>
                    <h3 className="text-lg font-semibold text-slate-800">{t('title')}</h3>
                    <p className="text-sm text-slate-500">{t('description')}</p>
                </div>
                <button className="bg-brand-primary hover:bg-brand-secondary text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2">
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
                        {webhooks.map((hook) => (
                            <tr key={hook.id}>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="text-sm font-medium text-slate-900">{hook.url}</div>
                                    <div className="text-xs text-slate-500">Dernier appel: {hook.lastTriggered || t('table.never')}</div>
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
                                        onClick={() => toggleWebhook(hook.id)}
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
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
