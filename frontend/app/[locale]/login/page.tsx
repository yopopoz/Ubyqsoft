"use client";

import { useState } from "react";
import Image from "next/image";
import { useRouter } from "@/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { useTranslations } from "next-intl";
import LanguageSwitcher from "@/components/LanguageSwitcher";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const router = useRouter();
    const t = useTranslations('Login');

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
                setError(data.detail || t('errorInvalid'));
            }
        } catch (e) {
            console.error("Login successful but error during state update:", e);
            setError(t('errorGeneric'));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex font-sans selection:bg-[#D30026] selection:text-white">
            {/* Left Panel - Branding (Premium White) */}
            <div className="hidden lg:flex lg:w-1/2 bg-[#F8FAFC] relative overflow-hidden flex-col items-center justify-center text-slate-900 border-r border-slate-100">
                {/* Background Pattern - Subtle & Premium */}
                <div className="absolute inset-0 opacity-[0.03] bg-[url('/grid.svg')] bg-center" />
                <div className="absolute inset-0 opacity-40 bg-[radial-gradient(#94a3b8_1px,transparent_1px)] [background-size:40px_40px]" />

                {/* Elegant Accents */}
                <div className="absolute top-0 left-0 w-1/4 h-1.5 bg-[#D30026]" />
                <div className="absolute bottom-0 right-0 w-1/4 h-1.5 bg-[#D30026]" />

                {/* Content */}
                <div className="relative z-10 flex flex-col justify-center px-12 items-center text-center w-full max-w-2xl">
                    <div className="mb-12 relative w-64 h-24 hover:scale-105 transition-transform duration-700">
                        <Image
                            src="/logo.png"
                            alt="PURE TRADE"
                            fill
                            className="object-contain"
                            priority
                            sizes="(max-width: 768px) 100vw, 50vw"
                        />
                    </div>

                    <div className="space-y-3 animate-slide-up w-full">
                        <h1 className="text-lg lg:text-xl font-medium tracking-widest text-slate-800 uppercase whitespace-nowrap">
                            {t('tagline1')}
                        </h1>
                        <h1 className="text-xl lg:text-2xl font-bold tracking-widest text-[#D30026] uppercase whitespace-nowrap">
                            {t('tagline2')}
                        </h1>
                    </div>

                    <div className="mt-16 w-12 h-1 bg-slate-200 rounded-full" />
                </div>
            </div>

            {/* Right Panel - Login Form (White) */}
            <div className="flex-1 flex flex-col items-center justify-center p-8 bg-white relative">
                <div className="absolute top-4 right-4">
                    <LanguageSwitcher />
                </div>
                <div className="w-full max-w-md animate-fade-in bg-white p-12 rounded-3xl shadow-[0_0_50px_rgba(0,0,0,0.03)] border border-slate-50 relative z-10">
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
                        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">{t('title')}</h2>
                        <p className="text-slate-700 mt-2 font-medium">{t('prompt')}</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-2">{t('emailLabel')}</label>
                            <input
                                id="email"
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-[#D30026]/20 focus:border-[#D30026] transition-all duration-200"
                                placeholder={t('emailPlaceholder')}
                            />
                        </div>

                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-2">{t('passwordLabel')}</label>
                            <input
                                id="password"
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-900 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-[#D30026]/20 focus:border-[#D30026] transition-all duration-200"
                                placeholder={t('passwordPlaceholder')}
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
                                    {t('submitLoading')}
                                </span>
                            ) : (
                                t('submit')
                            )}
                        </button>
                    </form>
                </div>

                {/* Footer Copyright */}
                <div className="absolute bottom-8 left-0 right-0 text-center">
                    <p className="text-sm font-medium text-slate-600">
                        {t('footer')}
                    </p>
                </div>
            </div>
        </div>
    );
}
