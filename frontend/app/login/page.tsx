"use client";

import { useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: new URLSearchParams({ username: email, password }),
            });

            const data = await res.json();

            if (res.ok && data.access_token) {
                localStorage.setItem("token", data.access_token);
                router.push("/");
                router.refresh();
            } else {
                setError(data.detail || "Identifiants invalides");
            }
        } catch {
            setError("Erreur de connexion. Veuillez réessayer.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex">
            {/* Left Panel - Branding */}
            <div className="hidden lg:flex lg:w-1/2 bg-white relative overflow-hidden flex-col items-center justify-center border-r border-slate-200">
                {/* Background Pattern */}
                <div className="absolute inset-0 opacity-5 bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:16px_16px]" />

                {/* Content */}
                <div className="relative z-10 flex flex-col justify-center px-16 items-center text-center max-w-xl">
                    <div className="mb-10 relative w-64 h-24">
                        <Image
                            src="/logo.png"
                            alt="PURE TRADE"
                            fill
                            className="object-contain"
                            priority
                            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                        />
                    </div>

                    <h2 className="text-3xl font-bold text-slate-900 mb-4">Logistique Mondiale</h2>
                    <p className="text-lg text-slate-500 mb-12">
                        Gérez vos expéditions, suivez vos conteneurs et analysez vos performances avec la plateforme PURE TRADE.
                    </p>

                    <div className="space-y-6 text-slate-500 text-left w-full">
                        <div className="flex items-center gap-4 p-4 rounded-xl bg-slate-50 border border-slate-100 shadow-sm">
                            <div className="h-10 w-10 rounded-lg bg-red-50 flex items-center justify-center flex-shrink-0 text-brand-secondary">
                                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                            </div>
                            <div>
                                <h3 className="font-semibold text-slate-800">Suivi en temps réel</h3>
                                <p className="text-sm">Suivez vos expéditions à travers le monde</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-4 p-4 rounded-xl bg-slate-50 border border-slate-100 shadow-sm">
                            <div className="h-10 w-10 rounded-lg bg-red-50 flex items-center justify-center flex-shrink-0 text-brand-secondary">
                                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                            </div>
                            <div>
                                <h3 className="font-semibold text-slate-800">Analyses avancées</h3>
                                <p className="text-sm">Rapports détaillés et insights exploitables</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Decorative Footer Line */}
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-brand-secondary" />
            </div>

            {/* Right Panel - Login Form */}
            <div className="flex-1 flex items-center justify-center p-8 bg-slate-50">
                <div className="w-full max-w-md">
                    <div className="text-center mb-8">
                        <div className="lg:hidden mb-8 relative w-48 h-16 mx-auto">
                            <Image
                                src="/logo.png"
                                alt="PURE TRADE"
                                fill
                                className="object-contain"
                                priority
                            />
                        </div>
                        <h2 className="text-2xl font-bold text-slate-900">Bienvenue</h2>
                        <p className="text-slate-500 mt-2">Connectez-vous pour accéder à votre tableau de bord</p>
                    </div>

                    <div className="card p-8 bg-white shadow-xl border border-slate-100 rounded-2xl">
                        <form onSubmit={handleSubmit} className="space-y-5">
                            <div>
                                <label htmlFor="email" className="input-label font-medium text-slate-700">Adresse email</label>
                                <input
                                    id="email"
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="input mt-1 block w-full rounded-lg border-slate-300 shadow-sm focus:border-brand-secondary focus:ring-brand-secondary"
                                    placeholder="vous@entreprise.com"
                                />
                            </div>

                            <div>
                                <label htmlFor="password" className="input-label font-medium text-slate-700">Mot de passe</label>
                                <input
                                    id="password"
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="input mt-1 block w-full rounded-lg border-slate-300 shadow-sm focus:border-brand-secondary focus:ring-brand-secondary"
                                    placeholder="••••••••"
                                />
                            </div>

                            {error && (
                                <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm animate-scale-in">
                                    <svg className="h-5 w-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    {error}
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-3 px-4 bg-brand-secondary hover:bg-red-700 text-white font-bold rounded-lg shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? (
                                    <span className="flex items-center justify-center gap-2">
                                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                        </svg>
                                        Connexion en cours...
                                    </span>
                                ) : (
                                    "Se connecter"
                                )}
                            </button>
                        </form>

                        {/* Demo credentials removed for production */}
                    </div>

                    <p className="text-center text-xs text-slate-400 mt-8">
                        © 2026 PURE TRADE. Tous droits réservés.
                    </p>
                </div>
            </div>
        </div>
    );
}
