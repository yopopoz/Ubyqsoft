"use client";

import { useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
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
                login(data.access_token);
            } else {
                setError(data.detail || "Identifiants invalides");
            }
        } catch (e) {
            console.error("Login successful but error during state update:", e);
            setError("Erreur de connexion. Veuillez réessayer.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex font-sans">
            {/* Left Panel - Branding (Premium White) */}
            <div className="hidden lg:flex lg:w-1/2 bg-[#F8FAFC] relative overflow-hidden flex-col items-center justify-center text-slate-900 border-r border-slate-200">
                {/* Background Pattern */}
                <div className="absolute inset-0 opacity-40 bg-[radial-gradient(#cbd5e1_1px,transparent_1px)] [background-size:32px_32px]" />

                {/* Red Accent Lines */}
                <div className="absolute top-0 left-0 w-1/3 h-1 bg-[#D30026]" />
                <div className="absolute bottom-0 right-0 w-full h-1 bg-[#D30026]" />

                {/* Content */}
                <div className="relative z-10 flex flex-col justify-center px-16 items-center text-center max-w-xl">
                    <div className="mb-12 relative w-64 h-24">
                        <Image
                            src="/logo.png"
                            alt="PURE TRADE"
                            fill
                            className="object-contain"
                            priority
                            sizes="(max-width: 768px) 100vw, 50vw"
                        />
                    </div>

                    <h1 className="text-4xl font-light tracking-widest mb-2 uppercase">
                        PROJET D'EXCEPTION
                    </h1>
                    <h1 className="text-4xl font-bold tracking-widest mb-8 text-[#D30026] uppercase">
                        SOLUTION D'EXCEPTION
                    </h1>

                    <p className="text-slate-500 mb-12 text-lg font-light leading-relaxed">
                        Plateforme de gestion unifiée pour vos opérations de transport international.
                    </p>

                    <div className="grid grid-cols-2 gap-6 w-full">
                        <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-sm text-left hover:border-[#D30026]/50 transition-colors">
                            <div className="h-10 w-10 rounded-lg bg-[#D30026] text-white flex items-center justify-center mb-4">
                                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                            </div>
                            <h3 className="font-semibold text-slate-900 mb-1">Temps Réel</h3>
                            <p className="text-slate-500 text-sm">Suivi précis des conteneurs</p>
                        </div>
                        <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-sm text-left hover:border-[#D30026]/50 transition-colors">
                            <div className="h-10 w-10 rounded-lg bg-slate-800 text-white flex items-center justify-center mb-4">
                                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                </svg>
                            </div>
                            <h3 className="font-semibold text-slate-900 mb-1">Analytics</h3>
                            <p className="text-slate-500 text-sm">Performance par transporteur</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Right Panel - Login Form (White) */}
            <div className="flex-1 flex items-center justify-center p-8 bg-white">
                <div className="w-full max-w-md animate-fade-in bg-white p-10 rounded-2xl shadow-none">
                    <div className="text-center mb-10">
                        <div className="lg:hidden mb-8 relative w-40 h-16 mx-auto">
                            <Image
                                src="/logo.png"
                                alt="PURE TRADE"
                                fill
                                className="object-contain"
                                priority
                            />
                        </div>
                        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Espace Client</h2>
                        <p className="text-slate-500 mt-2">Connectez-vous à votre compte Pure Trade</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-2">Email professionnel</label>
                            <input
                                id="email"
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#D30026]/20 focus:border-[#D30026] transition-all duration-200"
                                placeholder="nom@pure-trade.com"
                            />
                        </div>

                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-2">Mot de passe</label>
                            <input
                                id="password"
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#D30026]/20 focus:border-[#D30026] transition-all duration-200"
                                placeholder="••••••••"
                            />
                        </div>

                        {error && (
                            <div className="flex items-center gap-2 p-4 rounded-lg bg-red-50 border border-red-100 text-red-600 text-sm animate-flash">
                                <svg className="h-5 w-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3.5 px-6 bg-[#D30026] hover:bg-[#b91c1c] text-white font-semibold text-lg rounded-lg shadow-lg shadow-red-600/20 transition-all transform hover:-translate-y-0.5 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none"
                        >
                            {loading ? (
                                <span className="flex items-center justify-center gap-2">
                                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                    </svg>
                                    Connexion...
                                </span>
                            ) : (
                                "Se connecter"
                            )}
                        </button>
                    </form>

                    <p className="text-center text-xs text-slate-400 mt-8">
                        © 2026 Pure Trade. Tous droits réservés.
                    </p>
                </div>
            </div>
        </div>
    );
}
