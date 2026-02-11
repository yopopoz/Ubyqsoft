"use client";

import { useState, Suspense } from "react";
import CloudSettings from "@/components/settings/CloudSettings";
import WebhookSettings from "@/components/settings/WebhookSettings";
import AISettings from "@/components/settings/AISettings";
import EmailSettings from "@/components/settings/EmailSettings";
import SecuritySettings from "@/components/settings/SecuritySettings";
import LogisticsSettings from "@/components/settings/LogisticsSettings";

import { useTranslations } from "next-intl";

export default function AdminSettingsPage() {
    const t = useTranslations('Settings');
    const [activeTab, setActiveTab] = useState('cloud');

    const TABS = [
        { id: 'cloud', label: t('tabs.cloud'), icon: '☁️' },
        { id: 'logistics', label: t('tabs.logistics'), icon: '🚢' },
        { id: 'ai', label: t('tabs.ai'), icon: '✨' },
        { id: 'webhooks', label: t('tabs.webhooks'), icon: '🔗' },
        { id: 'email', label: t('tabs.email'), icon: '📧' },
        { id: 'security', label: t('tabs.security'), icon: '🔒' },
    ];

    const renderContent = () => {
        switch (activeTab) {
            case 'cloud': return (
                <Suspense fallback={<div className="p-8 text-center text-slate-700 font-bold">{t('loading')}</div>}>
                    <CloudSettings />
                </Suspense>
            );
            case 'logistics': return <LogisticsSettings />;
            case 'ai': return <AISettings />;
            case 'webhooks': return <WebhookSettings />;
            case 'email': return <EmailSettings />;
            case 'security': return <SecuritySettings />;
            default: return <CloudSettings />;
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-slate-900">{t('title')}</h1>
                <p className="text-slate-700 font-medium">{t('description')}</p>
            </div>

            <div className="flex flex-col lg:flex-row gap-8">
                {/* Sidebar Tabs */}
                <div className="w-full lg:w-64 flex-shrink-0">
                    <nav className="space-y-1">
                        {TABS.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${activeTab === tab.id
                                    ? 'bg-brand-primary/10 text-brand-primary shadow-sm'
                                    : 'text-slate-700 hover:bg-slate-50 hover:text-slate-900 font-bold'
                                    }`}
                            >
                                <span className="text-lg">{tab.icon}</span>
                                {tab.label}
                            </button>
                        ))}
                    </nav>
                </div>

                {/* Main Content Area */}
                <div className="flex-1 min-w-0">
                    {renderContent()}
                </div>
            </div>
        </div>
    );
}
