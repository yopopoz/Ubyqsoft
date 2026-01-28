"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { navigation } from "@/config/navigation";

interface SidebarProps {
    onClose?: () => void;
}

export default function Sidebar({ onClose }: SidebarProps) {
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
                return { bg: "bg-black", text: "text-white", label: "Admin" }; // High contrast for admin
            case "ops":
                return { bg: "bg-zinc-200", text: "text-black", label: "Opérateur" }; // Subtle for ops
            default:
                return { bg: "bg-zinc-100", text: "text-zinc-500", label: "Client" };
        }
    };

    const roleBadge = getRoleBadge(user?.role || "client");

    return (
        <div className="w-64 flex-shrink-0 h-full border-r border-zinc-200 shadow-sm relative overflow-hidden bg-white text-black z-50 flex flex-col">
            {/* Logo */}
            <div className="flex items-center justify-center pt-8 pb-6 px-6 bg-white shrink-0">
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

            {/* Navigation */}
            <nav className="flex-1 px-4 py-4 space-y-2 overflow-y-auto">
                <p className="px-4 py-2 text-xs font-bold text-zinc-400 uppercase tracking-widest">
                    Menu
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
                            <span className={`transition-colors duration-200 ${isActive ? "text-black" : "text-zinc-400 group-hover:text-black"}`}>
                                {item.icon}
                            </span>
                            <span className="font-medium text-sm tracking-wide">{item.name}</span>
                        </Link>
                    );
                })}
            </nav>

            {/* User Section - Minimalist */}
            <div className="p-4 border-t border-zinc-100 bg-white shrink-0">
                <div className="flex items-center gap-3 p-3 rounded-xl bg-zinc-50 border border-zinc-100 transition-all hover:bg-zinc-100">
                    <div className="h-10 w-10 rounded-full bg-black text-white flex items-center justify-center font-bold text-sm flex-shrink-0">
                        {(user?.sub || "U").charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-bold text-black truncate">
                            {user?.sub?.split("@")[0] || "Utilisateur"}
                        </p>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${roleBadge.bg} ${roleBadge.text}`}>
                            {roleBadge.label}
                        </span>
                    </div>
                    <button
                        onClick={logout}
                        className="p-2 rounded-lg text-zinc-400 hover:text-black hover:bg-white transition-all shadow-sm flex-shrink-0"
                        title="Déconnexion"
                    >
                        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    );
}
