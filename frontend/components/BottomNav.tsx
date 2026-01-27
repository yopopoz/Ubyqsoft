"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { navigation } from "@/config/navigation";

export default function BottomNav() {
    const pathname = usePathname();
    const { canWrite, isAdmin } = useAuth();

    const visibleNav = navigation.filter((item) => {
        if (item.requiresAdmin) return isAdmin;
        if (item.requiresWrite) return canWrite;
        return true;
    });

    return (
        <div className="lg:hidden fixed bottom-6 left-6 right-6 bg-white/90 backdrop-blur-md border border-white/20 pb-safe-area p-2 z-50 shadow-2xl rounded-2xl ring-1 ring-slate-900/5">
            <div className="flex justify-around items-center">
                {visibleNav.map((item) => {
                    const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={`flex flex-col items-center justify-center p-2 rounded-xl transition-all duration-300 group ${isActive ? "text-brand-secondary bg-brand-secondary/5" : "text-slate-400 hover:text-slate-600 hover:bg-slate-50"}`}
                        >
                            <div className={`transition-transform duration-300 ${isActive ? "-translate-y-0.5 scale-110" : ""}`}>
                                {item.icon}
                            </div>
                            {/* Use name but maybe truncate or use a map if too long? "Tableau de bord" is ok-ish. */}
                            <span className="text-[10px] font-medium mt-1 truncate max-w-[80px]">{item.shortName}</span>
                        </Link>
                    );
                })}
            </div>
        </div>
    );
}
