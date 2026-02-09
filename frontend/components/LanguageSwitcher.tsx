
'use client';

import { useLocale } from 'next-intl';
import { useRouter, usePathname } from '@/navigation';
import { ChangeEvent, useTransition } from 'react';

export default function LanguageSwitcher({ className }: { className?: string }) {
    const [isPending, startTransition] = useTransition();
    const locale = useLocale();
    const router = useRouter();
    const pathname = usePathname();

    const onSelectChange = (e: ChangeEvent<HTMLSelectElement>) => {
        const nextLocale = e.target.value;
        startTransition(() => {
            router.replace(pathname, { locale: nextLocale });
        });
    };

    return (
        <label className={`inline-flex items-center ${className}`}>
            <select
                defaultValue={locale}
                className="bg-transparent py-1 px-2 rounded border border-slate-300 text-slate-700 text-sm focus:outline-none focus:ring-2 focus:ring-[#D30026]/20 cursor-pointer"
                onChange={onSelectChange}
                disabled={isPending}
            >
                <option value="en">EN</option>
                <option value="fr">FR</option>
            </select>
        </label>
    );
}
