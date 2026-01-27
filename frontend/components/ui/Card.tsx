import React from 'react';

interface CardProps {
    children: React.ReactNode;
    className?: string;
    hover?: boolean;
    style?: React.CSSProperties;
}

export function Card({ children, className = '', hover = false, style }: CardProps) {
    // Determine if background class is provided, otherwise default to bg-white
    const hasBg = className.includes('bg-') || className.includes('glass');
    const baseClasses = `rounded-xl border border-surface-3 shadow-sm p-5 ${hasBg ? '' : 'bg-white'}`;

    return (
        <div
            className={`
        ${baseClasses}
        ${hover ? 'card-hover-effect cursor-pointer' : ''}
        ${className}
      `}
            style={style}
        >
            {children}
        </div>
    );
}

export function CardHeader({ title, action }: { title: string; action?: React.ReactNode }) {
    return (
        <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-brand-primary">{title}</h3>
            {action && <div>{action}</div>}
        </div>
    );
}
