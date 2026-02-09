"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

export default function SecuritySettings() {
    const t = useTranslations('Settings.Security');
    const [apiKeys, setApiKeys] = useState([
        { id: '1', name: 'Mobile App Prod', prefix: 'pk_live_...', created: '2023-10-15', lastUsed: 'Il y a 2 minutes' },
        { id: '2', name: 'Partner Integration', prefix: 'pk_live_...', created: '2023-11-01', lastUsed: 'Il y a 2 jours' },
    ]);

    return (
        <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h3 className="text-lg font-semibold text-slate-800">{t('title')}</h3>
                        <p className="text-sm text-slate-500">{t('description')}</p>
                    </div>
                    <button className="bg-brand-primary hover:bg-brand-secondary text-white px-4 py-2 rounded-lg font-medium transition-colors">
                        {t('generate')}
                    </button>
                </div>

                <div className="space-y-4">
                    {apiKeys.map((key) => (
                        <div key={key.id} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
                            <div>
                                <h4 className="font-medium text-slate-900">{key.name}</h4>
                                <div className="flex items-center gap-4 mt-1">
                                    <code className="bg-white px-2 py-0.5 rounded border border-slate-200 text-xs font-mono text-slate-600">
                                        {key.prefix}****************
                                    </code>
                                    <span className="text-xs text-slate-500">{t('created', { date: key.created })}</span>
                                </div>
                            </div>
                            <div className="flex items-center gap-4">
                                <span className="text-xs text-slate-500">
                                    {key.lastUsed.startsWith('Il y a') ? key.lastUsed : t('lastUsed', { time: key.lastUsed })}
                                </span>
                                <button className="text-red-600 hover:text-red-700 text-sm font-medium">
                                    {t('revoke')}
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
