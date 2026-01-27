"use client";

import { useState, Suspense } from "react";
import CloudSettings from "@/components/settings/CloudSettings";
import WebhookSettings from "@/components/settings/WebhookSettings";
import AISettings from "@/components/settings/AISettings";
import EmailSettings from "@/components/settings/EmailSettings";
import SecuritySettings from "@/components/settings/SecuritySettings";

const TABS = [
    { id: 'cloud', label: 'Cloud & Intégrations', icon: '☁️' },
    { id: 'ai', label: 'Intelligence Artificielle', icon: '✨' },
    { id: 'webhooks', label: 'Webhooks', icon: '🔗' },
    { id: 'email', label: 'Email & SMTP', icon: '📧' },
    { id: 'security', label: 'Sécurité & API', icon: '🔒' },
];

export default function AdminSettingsPage() {
    const [activeTab, setActiveTab] = useState('cloud');

    const renderContent = () => {
        switch (activeTab) {
            case 'cloud': return (
                <Suspense fallback={<div className="p-8 text-center text-slate-500">Chargement des paramètres cloud...</div>}>
                    <CloudSettings />
                </Suspense>
            );
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
                <h1 className="text-2xl font-bold text-slate-900">Paramètres de l'application</h1>
                <p className="text-slate-500">Gérez les configurations globales et les intégrations système.</p>
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
                                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
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
