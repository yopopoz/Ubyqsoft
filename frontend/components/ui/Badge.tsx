import React from 'react';

type BadgeVariant = 'success' | 'warning' | 'error' | 'info' | 'neutral' | 'brand';

interface BadgeProps {
    children: React.ReactNode;
    variant?: BadgeVariant;
    className?: string;
    icon?: React.ReactNode;
}

const variants: Record<BadgeVariant, string> = {
    success: "bg-emerald-100/80 text-emerald-700 border-emerald-200",
    warning: "bg-amber-100/80 text-amber-700 border-amber-200",
    error: "bg-red-100/80 text-red-700 border-red-200",
    info: "bg-slate-100/80 text-slate-700 border-slate-200", // Softened from blue
    neutral: "bg-slate-100/80 text-slate-600 border-slate-200",
    brand: "bg-red-50 text-red-700 border-red-100", // Matches brand-secondary light version
};

export function Badge({ children, variant = 'neutral', className = '', icon }: BadgeProps) {
    const variantStyles = variants[variant] || variants.neutral;

    return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${variantStyles} ${className}`}>
            {icon && <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70" />}
            {children}
        </span>
    );
}
