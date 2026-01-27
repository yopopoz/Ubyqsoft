"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { navigation } from "@/config/navigation";

export default function Sidebar() {
    const pathname = usePathname();
    const { canWrite, isAdmin, user, logout } = useAuth();

    const visibleNav = navigation.filter((item) => {
        if (item.requiresAdmin) return isAdmin;
        if (item.requiresWrite) return canWrite;
        return true;
    });

    const getRoleBadge = (role: string) => {
        switch (role) {
            case "admin":
                return { bg: "bg-red-500/10", text: "text-red-700", label: "Admin" };
            case "ops":
                return { bg: "bg-slate-500/10", text: "text-slate-700", label: "Opérateur" };
            default:
                return { bg: "bg-slate-400/10", text: "text-slate-500", label: "Client" };
        }
    };

    const roleBadge = getRoleBadge(user?.role || "client");

    return (
        <div className="w-64 flex-shrink-0 h-full border-r border-slate-100 shadow-[4px_0_24px_rgba(0,0,0,0.02)] relative overflow-hidden bg-white text-slate-800 z-50">
            {/* Logo */}
            <div className="flex items-center justify-between px-6 py-8 relative z-10 bg-white">
                <div className="flex items-center justify-center w-full">
                    <div className="relative w-40 h-16">
                        <Image
                            src="/logo.png"
                            alt="PURE TRADE"
                            fill
                            className="object-contain" // Preserves aspect ratio
                            priority
                        />
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
                <p className="px-3 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Navigation
                </p>
                {visibleNav.map((item) => {
                    const isActive = pathname === item.href ||
                        (item.href !== "/" && pathname.startsWith(item.href));

                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={isActive ? "sidebar-nav-item-active group" : "sidebar-nav-item-inactive group"}
                        >
                            <span className={`transition-colors duration-200 ${isActive ? "text-brand-secondary" : "text-slate-400 group-hover:text-slate-600"}`}>
                                {item.icon}
                            </span>
                            <span className="font-medium text-sm">{item.name}</span>
                        </Link>
                    );
                })}
            </nav>

            {/* User Section */}
            <div className="p-3 border-t border-slate-100">
                <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                    <div className="h-9 w-9 rounded-full bg-brand-primary text-white flex items-center justify-center font-semibold text-sm flex-shrink-0 shadow-sm">
                        {(user?.sub || "U").charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 truncate">
                            {user?.sub?.split("@")[0] || "Utilisateur"}
                        </p>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${roleBadge.bg} ${roleBadge.text}`}>
                            {roleBadge.label}
                        </span>
                    </div>
                    <button
                        onClick={logout}
                        className="p-2 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors flex-shrink-0"
                        title="Déconnexion"
                    >
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    );
}
