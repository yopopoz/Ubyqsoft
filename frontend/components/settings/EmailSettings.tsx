"use client";

import { useTranslations } from "next-intl";
import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { apiFetch } from "@/services/api";

export default function EmailSettings() {
    const t = useTranslations('Settings.Email');
    const { token } = useAuth();
    const [isLoading, setIsLoading] = useState(false);

    // Form State
    const [host, setHost] = useState("");
    const [port, setPort] = useState("587");
    const [security, setSecurity] = useState("STARTTLS");
    const [user, setUser] = useState("");
    const [password, setPassword] = useState("");

    useEffect(() => {
        if (!token) return;
        const loadSettings = async () => {
            setIsLoading(true);
            try {
                const data = await apiFetch<Record<string, unknown>>('/settings/', { token });
                if (data.SMTP_HOST) setHost(data.SMTP_HOST);
                if (data.SMTP_PORT) setPort(data.SMTP_PORT);
                if (data.SMTP_SECURITY) setSecurity(data.SMTP_SECURITY);
                if (data.SMTP_USER) setUser(data.SMTP_USER);
                // We don't load the password for security, or we load it but don't show it?
                // Typically passwords aren't returned or are masked.
                // For this simple implementation, if it returns it (encrypted), we might not want to display it directly.
                // But the backend `get_all_settings` returns decrypted values if `is_encrypted` logic is simple.
                // The current backend simplisticly returns everything.
                if (data.SMTP_PASSWORD) setPassword(data.SMTP_PASSWORD);
            } catch (e) {
                console.error("Failed to load email settings", e);
            } finally {
                setIsLoading(false);
            }
        };
        loadSettings();
    }, [token]);

    const handleSave = async () => {
        if (!token) return;
        setIsLoading(true);
        try {
            await apiFetch('/settings/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify([
                    { key: "SMTP_HOST", value: host },
                    { key: "SMTP_PORT", value: port },
                    { key: "SMTP_SECURITY", value: security },
                    { key: "SMTP_USER", value: user },
                    { key: "SMTP_PASSWORD", value: password, is_encrypted: true }
                ]),
                token
            });
            alert("Paramètres enregistrés avec succès");
        } catch (e) {
            console.error(e);
            alert("Erreur lors de l'enregistrement");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="max-w-2xl space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
                <h3 className="text-lg font-semibold text-slate-800 mb-6">{t('title')}</h3>

                {isLoading && <div className="text-sm text-blue-500 mb-4">Chargement...</div>}

                <div className="grid grid-cols-1 gap-6">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">{t('server')}</label>
                        <input
                            type="text"
                            value={host}
                            onChange={(e) => setHost(e.target.value)}
                            className="w-full rounded-lg border-slate-300 focus:ring-brand-primary focus:border-brand-primary"
                            placeholder="smtp.office365.com"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">{t('port')}</label>
                            <input
                                type="text"
                                value={port}
                                onChange={(e) => setPort(e.target.value)}
                                className="w-full rounded-lg border-slate-300 focus:ring-brand-primary focus:border-brand-primary"
                                placeholder="587"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">{t('security')}</label>
                            <select
                                value={security}
                                onChange={(e) => setSecurity(e.target.value)}
                                className="w-full rounded-lg border-slate-300 focus:ring-brand-primary focus:border-brand-primary"
                            >
                                <option value="STARTTLS">STARTTLS</option>
                                <option value="SSL/TLS">SSL/TLS</option>
                                <option value="NONE">{t('none')}</option>
                            </select>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">{t('sender')}</label>
                        <input
                            type="email"
                            value={user}
                            onChange={(e) => setUser(e.target.value)}
                            className="w-full rounded-lg border-slate-300 focus:ring-brand-primary focus:border-brand-primary"
                            placeholder="notifications@bboxl.com"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">{t('password')}</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full rounded-lg border-slate-300 focus:ring-brand-primary focus:border-brand-primary"
                            placeholder="••••••••••••••••"
                        />
                    </div>

                    <div className="pt-4 flex items-center justify-between">
                        <button
                            className="text-brand-primary hover:text-brand-secondary text-sm font-medium opacity-50 cursor-not-allowed"
                            disabled
                            title="Non implémenté"
                        >
                            {t('test')}
                        </button>
                        <button
                            onClick={handleSave}
                            disabled={isLoading}
                            className="bg-brand-primary hover:bg-brand-secondary text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
                        >
                            {isLoading ? "Enregistrement..." : t('save')}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
