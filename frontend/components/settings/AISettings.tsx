"use client";

import { useState, useEffect } from "react";
import { apiFetch } from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";

type AIProvider = 'gemini' | 'claude' | 'openai';

interface AIConfig {
    provider: AIProvider;
    apiKey: string;
    model: string;
    enabled: boolean;
}

export default function AISettings() {
    const [configs, setConfigs] = useState<Record<AIProvider, AIConfig>>({
        gemini: { provider: 'gemini', apiKey: '', model: 'gemini-pro', enabled: false },
        claude: { provider: 'claude', apiKey: '', model: 'claude-3-opus', enabled: false },
        openai: { provider: 'openai', apiKey: '', model: 'gpt-4-turbo', enabled: false },
    });

    const [prompts, setPrompts] = useState({
        chatbot: "",
        predictive: ""
    });

    const { token } = useAuth();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        console.log("AISettings mounted/updated. Token:", token ? "Present" : "Missing");
        if (token) {
            loadSettings();
        } else {
            // Failsafe: if no token after 2 seconds, stop loading
            const timer = setTimeout(() => {
                console.log("No token after timeout, stopping loading");
                setLoading(false);
            }, 2000);
            return () => clearTimeout(timer);
        }
    }, [token]);

    const loadSettings = async () => {
        if (!token) return;
        try {
            console.log("Fetching settings...");
            const data = await apiFetch<any>('/settings/', { token });
            console.log("Settings fetched:", data);

            // Map backend simple KEY-VALUE to structured state
            // Assumes keys like AI_GEMINI_KEY, AI_GEMINI_MODEL, AI_GEMINI_ENABLED

            setConfigs(prev => {
                const next = { ...prev };
                (['gemini', 'claude', 'openai'] as AIProvider[]).forEach(prov => {
                    next[prov] = {
                        provider: prov,
                        apiKey: data[`AI_${prov.toUpperCase()}_KEY`] || '',
                        model: data[`AI_${prov.toUpperCase()}_MODEL`] || next[prov].model,
                        enabled: data[`AI_${prov.toUpperCase()}_ENABLED`] === 'true'
                    };
                });
                return next;
            });

            setPrompts({
                chatbot: data['AI_PROMPT_CHATBOT'] || "",
                predictive: data['AI_PROMPT_PREDICTIVE'] || ""
            });
        } catch (e) {
            console.error("Failed to load settings", e);
        } finally {
            setLoading(false);
        }
    };

    const saveSettings = async () => {
        setSaving(true);
        try {
            const updates = [];

            // Prepare updates for providers
            Object.values(configs).forEach(conf => {
                updates.push({ key: `AI_${conf.provider.toUpperCase()}_KEY`, value: conf.apiKey, is_encrypted: true });
                updates.push({ key: `AI_${conf.provider.toUpperCase()}_MODEL`, value: conf.model });
                updates.push({ key: `AI_${conf.provider.toUpperCase()}_ENABLED`, value: String(conf.enabled) });
            });

            // Prepare updates for prompts
            updates.push({ key: 'AI_PROMPT_CHATBOT', value: prompts.chatbot });
            updates.push({ key: 'AI_PROMPT_PREDICTIVE', value: prompts.predictive });

            await apiFetch('/settings/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates),
                token
            });

            alert("Configuration sauvegardée !");
        } catch (e) {
            console.error("Failed to save", e);
            alert("Erreur lors de la sauvegarde");
        } finally {
            setSaving(false);
        }
    };

    const handleConfigChange = (provider: AIProvider, field: keyof AIConfig, value: any) => {
        setConfigs(prev => ({
            ...prev,
            [provider]: { ...prev[provider], [field]: value }
        }));
    };

    if (loading) return <div>Chargement...</div>;

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold text-slate-900">Intelligence Artificielle</h2>
                <button
                    onClick={saveSettings}
                    disabled={saving}
                    className="bg-brand-primary hover:bg-brand-secondary text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
                >
                    {saving ? 'Sauvegarde...' : 'Sauvegarder tout'}
                </button>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">Fournisseurs</h3>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Gemini Config */}
                    <div className={`p-4 rounded-xl border-2 transition-all ${configs.gemini.enabled ? 'border-blue-500 bg-blue-50/10' : 'border-slate-200 opacity-75'}`}>
                        <div className="flex items-center justify-between mb-4">
                            <h4 className="font-semibold text-slate-700 flex items-center gap-2">
                                <span className="text-2xl">✨</span> Gemini
                            </h4>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input
                                    type="checkbox"
                                    className="sr-only peer"
                                    checked={configs.gemini.enabled}
                                    onChange={(e) => handleConfigChange('gemini', 'enabled', e.target.checked)}
                                />
                                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                            </label>
                        </div>
                        <div className="space-y-3">
                            <div>
                                <label className="block text-xs font-medium text-slate-500 mb-1">Clé API</label>
                                <input
                                    type="password"
                                    value={configs.gemini.apiKey}
                                    onChange={(e) => handleConfigChange('gemini', 'apiKey', e.target.value)}
                                    className="w-full text-sm border-slate-300 rounded-md focus:ring-brand-primary focus:border-brand-primary"
                                    placeholder="AIza..."
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-slate-500 mb-1">Modèle</label>
                                <select
                                    value={configs.gemini.model}
                                    onChange={(e) => handleConfigChange('gemini', 'model', e.target.value)}
                                    className="w-full text-sm border-slate-300 rounded-md focus:ring-brand-primary focus:border-brand-primary"
                                >
                                    <option value="gemini-pro">Gemini Pro 1.5</option>
                                    <option value="gemini-ultra">Gemini Ultra</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* Claude Config */}
                    <div className={`p-4 rounded-xl border-2 transition-all ${configs.claude.enabled ? 'border-orange-500 bg-orange-50/10' : 'border-slate-200 opacity-75'}`}>
                        <div className="flex items-center justify-between mb-4">
                            <h4 className="font-semibold text-slate-700 flex items-center gap-2">
                                <span className="text-2xl">🧠</span> Claude
                            </h4>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input
                                    type="checkbox"
                                    className="sr-only peer"
                                    checked={configs.claude.enabled}
                                    onChange={(e) => handleConfigChange('claude', 'enabled', e.target.checked)}
                                />
                                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-orange-600"></div>
                            </label>
                        </div>
                        <div className="space-y-3">
                            <div>
                                <label className="block text-xs font-medium text-slate-500 mb-1">Clé API</label>
                                <input
                                    type="password"
                                    value={configs.claude.apiKey}
                                    onChange={(e) => handleConfigChange('claude', 'apiKey', e.target.value)}
                                    className="w-full text-sm border-slate-300 rounded-md focus:ring-brand-primary focus:border-brand-primary"
                                    placeholder="sk-ant..."
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-slate-500 mb-1">Modèle</label>
                                <select
                                    value={configs.claude.model}
                                    onChange={(e) => handleConfigChange('claude', 'model', e.target.value)}
                                    className="w-full text-sm border-slate-300 rounded-md focus:ring-brand-primary focus:border-brand-primary"
                                >
                                    <option value="claude-3-opus">Claude 3 Opus</option>
                                    <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                                    <option value="claude-3-haiku">Claude 3 Haiku</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* OpenAI Config */}
                    <div className={`p-4 rounded-xl border-2 transition-all ${configs.openai.enabled ? 'border-green-500 bg-green-50/10' : 'border-slate-200 opacity-75'}`}>
                        <div className="flex items-center justify-between mb-4">
                            <h4 className="font-semibold text-slate-700 flex items-center gap-2">
                                <span className="text-2xl">🤖</span> ChatGPT
                            </h4>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input
                                    type="checkbox"
                                    className="sr-only peer"
                                    checked={configs.openai.enabled}
                                    onChange={(e) => handleConfigChange('openai', 'enabled', e.target.checked)}
                                />
                                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
                            </label>
                        </div>
                        <div className="space-y-3">
                            <div>
                                <label className="block text-xs font-medium text-slate-500 mb-1">Clé API</label>
                                <input
                                    type="password"
                                    value={configs.openai.apiKey}
                                    onChange={(e) => handleConfigChange('openai', 'apiKey', e.target.value)}
                                    className="w-full text-sm border-slate-300 rounded-md focus:ring-brand-primary focus:border-brand-primary"
                                    placeholder="sk-..."
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-slate-500 mb-1">Modèle</label>
                                <select
                                    value={configs.openai.model}
                                    onChange={(e) => handleConfigChange('openai', 'model', e.target.value)}
                                    className="w-full text-sm border-slate-300 rounded-md focus:ring-brand-primary focus:border-brand-primary"
                                >
                                    <option value="gpt-4-turbo">GPT-4 Turbo</option>
                                    <option value="gpt-4o">GPT-4o</option>
                                    <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Chatbot Prompt */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
                    <h3 className="text-lg font-semibold text-slate-800 mb-4">Prompt Système du Chatbot API</h3>
                    <p className="text-sm text-slate-500 mb-4">Définissez la personnalité et les connaissances de base de votre assistant virtuel.</p>
                    <textarea
                        className="w-full h-64 p-4 rounded-lg border-slate-200 focus:border-brand-primary focus:ring-brand-primary font-mono text-sm bg-slate-50"
                        value={prompts.chatbot}
                        onChange={(e) => setPrompts({ ...prompts, chatbot: e.target.value })}
                        placeholder="Tu es un expert..."
                    />
                </div>

                {/* Predictive AI Prompt */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
                    <h3 className="text-lg font-semibold text-slate-800 mb-4">Prompt d'Analyse Prédictive</h3>
                    <p className="text-sm text-slate-500 mb-4">Instructions pour l'analyse automatique des expéditions et des risques de retard.</p>
                    <textarea
                        className="w-full h-64 p-4 rounded-lg border-slate-200 focus:border-brand-primary focus:ring-brand-primary font-mono text-sm bg-slate-50"
                        value={prompts.predictive}
                        onChange={(e) => setPrompts({ ...prompts, predictive: e.target.value })}
                        placeholder="Analyse les données..."
                    />
                </div>
            </div>
        </div>
    );
}
