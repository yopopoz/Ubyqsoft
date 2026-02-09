"use client";

import { useAuth } from "@/contexts/AuthContext";
import { useState, useEffect } from "react";
import { useLocale, useTranslations } from "next-intl";
import LanguageSwitcher from "@/components/LanguageSwitcher";

interface NavbarProps {
    onMenuClick?: () => void;
}

export default function Navbar({ onMenuClick }: NavbarProps) {
    const { user } = useAuth();
    const [searchQuery, setSearchQuery] = useState("");
    const [currentTime, setCurrentTime] = useState<string>("");
    const [currentDate, setCurrentDate] = useState<string>("");
    const locale = useLocale();
    const t = useTranslations('Navbar');

    useEffect(() => {
        const updateTime = () => {
            const now = new Date();
            setCurrentDate(now.toLocaleDateString(locale, { weekday: "short", month: "short", day: "numeric" }));
            setCurrentTime(now.toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" }));
        };

        updateTime();
        const interval = setInterval(updateTime, 60000);

        return () => clearInterval(interval);
    }, [locale]);

    return (
        <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-sm border-b border-slate-200">
            <div className="flex h-14 sm:h-16 items-center justify-between px-4 sm:px-6">
                {/* Left: Menu button + Search */}
                <div className="flex items-center gap-3 flex-1">
                    {/* Hamburger Menu - Removed for Mobile Bottom Nav */}


                    {/* Search Bar */}
                    <div className="flex-1 max-w-md">
                        <div className="relative">
                            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                                <svg className="h-4 w-4 sm:h-5 sm:w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                            </div>
                            <input
                                type="text"
                                placeholder={t('searchPlaceholder')}
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="block w-full rounded-lg border-0 bg-slate-100 py-2 pl-9 sm:pl-10 pr-3 text-sm text-slate-900 placeholder-slate-400 focus:bg-white focus:ring-2 focus:ring-brand-secondary/20 focus:border-brand-secondary/50 transition-all"
                                suppressHydrationWarning
                            />
                        </div>
                    </div>
                </div>

                {/* Right Section */}
                <div className="flex items-center gap-2 sm:gap-3 ml-3">
                    <LanguageSwitcher />

                    {/* Notifications */}
                    <button className="relative p-2 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors">
                        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                        </svg>
                        <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-brand-secondary ring-2 ring-white" />
                    </button>

                    {/* Divider - Hidden on mobile */}
                    <div className="hidden sm:block h-6 w-px bg-slate-200" />

                    {/* Date/Time - Hidden on mobile */}
                    {(currentDate) && (
                        <div className="hidden md:flex flex-col items-end">
                            <span className="text-sm font-medium text-slate-700">{currentDate}</span>
                            <span className="text-xs text-slate-500">{currentTime}</span>
                        </div>
                    )}

                    {/* User Profile */}
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-primary text-sm font-bold text-white shadow-lg shadow-brand-primary/10 ring-2 ring-white ml-2 border border-white/10">
                        {user?.name?.charAt(0) || user?.email?.charAt(0) || "U"}
                    </div>
                </div>
            </div>
        </header>
    );
}
