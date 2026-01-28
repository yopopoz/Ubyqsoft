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
                // AuthContext handles router.push("/")
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
        <div className="min-h-screen flex bg-black text-white">
            {/* Left Panel - Branding */}
            <div className="hidden lg:flex lg:w-1/2 bg-black relative overflow-hidden flex-col items-center justify-center border-r border-zinc-800">
                {/* Background Pattern */}
                <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#ffffff_1px,transparent_1px)] [background-size:24px_24px]" />

                {/* Content */}
                <div className="relative z-10 flex flex-col justify-center px-16 items-center text-center max-w-xl">
                    <div className="mb-12 relative w-80 h-32">
                        {/* UBYQ Branding for Login Page */}
                        <Image
                            src="/ubyq-logo.png"
                            alt="UBYQ"
                            fill
                            className="object-contain"
                            priority
                            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                        />
                    </div>

                    <h1 className="text-white mb-6 tracking-tight">Logistique Mondiale</h1>
                    <p className="text-zinc-400 mb-12">
                        Gérez vos expéditions, suivez vos conteneurs et analysez vos performances avec la plateforme UBYQ.
                    </p>

                    <div className="space-y-6 text-zinc-300 text-left w-full">
                        <div className="flex items-center gap-5 p-5 rounded-2xl bg-zinc-900 border border-zinc-800 shadow-xl backdrop-blur-sm">
                            <div className="h-12 w-12 rounded-xl bg-white text-black flex items-center justify-center flex-shrink-0">
                                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                            </div>
                            <div>
                                <h3 className="text-white">Suivi en temps réel</h3>
                                <p className="text-zinc-400 text-base">Suivez vos expéditions à travers le monde</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-5 p-5 rounded-2xl bg-zinc-900 border border-zinc-800 shadow-xl backdrop-blur-sm">
                            <div className="h-12 w-12 rounded-xl bg-white text-black flex items-center justify-center flex-shrink-0">
                                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                            </div>
                            <div>
                                <h3 className="text-white">Analyses avancées</h3>
                                <p className="text-zinc-400 text-base">Rapports détaillés et insights exploitables</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Decorative Footer Line */}
                <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-zinc-700 to-transparent" />
            </div>

            {/* Right Panel - Login Form */}
            <div className="flex-1 flex items-center justify-center p-8 bg-black">
                <div className="w-full max-w-md animate-fade-in">
                    <div className="text-center mb-10">
                        <div className="lg:hidden mb-8 relative w-48 h-16 mx-auto">
                            <Image
                                src="/ubyq-logo.png"
                                alt="UBYQ"
                                fill
                                className="object-contain"
                                priority
                            />
                        </div>
                        <h2 className="text-white tracking-wide">Bienvenue</h2>
                        <p className="text-zinc-500 mt-3">Connectez-vous pour accéder à votre tableau de bord</p>
                    </div>

                    <div className="backdrop-blur-xl bg-zinc-900/30 p-8 shadow-2xl border border-zinc-800 rounded-3xl">
                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div>
                                <label htmlFor="email" className="block text-sm font-medium text-zinc-400 mb-2 ml-1">Adresse email</label>
                                <input
                                    id="email"
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl text-white placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-white focus:border-transparent transition-all duration-200"
                                    placeholder="vous@entreprise.com"
                                />
                            </div>

                            <div>
                                <label htmlFor="password" className="block text-sm font-medium text-zinc-400 mb-2 ml-1">Mot de passe</label>
                                <input
                                    id="password"
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl text-white placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-white focus:border-transparent transition-all duration-200"
                                    placeholder="••••••••"
                                />
                            </div>

                            {error && (
                                <div className="flex items-center gap-2 p-4 rounded-xl bg-red-950/30 border border-red-900/50 text-red-400 text-sm animate-flash">
                                    <svg className="h-5 w-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    {error}
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-4 px-6 bg-white hover:bg-zinc-200 text-black font-bold text-lg rounded-xl shadow-lg transition-all transform hover:-translate-y-1 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
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

                        {/* Demo credentials removed for production */}
                    </div>

                    <p className="text-center text-xs text-zinc-600 mt-10">
                        © 2026 UBYQ. Tous droits réservés.
                    </p>
                </div>
            </div>
        </div>
    );
}
