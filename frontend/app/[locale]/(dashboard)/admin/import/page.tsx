'use client';

import React, { useState } from 'react';
import ExcelImportModal from '@/components/ExcelImportModal';
import { useRouter } from 'next/navigation';

import { useTranslations } from 'next-intl';

export default function ImportPage() {
    const t = useTranslations('Import');
    const [isModalOpen, setIsModalOpen] = useState(true);
    const router = useRouter();

    const handleClose = () => {
        setIsModalOpen(false);
        router.push('/shipments');
    };

    const handleSuccess = () => {
        // Will refresh shipments list when navigating back
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8">
            <ExcelImportModal
                isOpen={isModalOpen}
                onClose={handleClose}
                onSuccess={handleSuccess}
            />

            {/* Fallback content if modal is closed */}
            {!isModalOpen && (
                <div className="flex flex-col items-center justify-center h-[60vh]">
                    <div className="p-6 rounded-2xl bg-slate-800/50 border border-slate-700/50 text-center">
                        <h2 className="text-xl font-semibold text-white mb-4">{t('title')}</h2>
                        <button
                            onClick={() => setIsModalOpen(true)}
                            className="px-6 py-3 rounded-lg font-medium bg-gradient-to-r from-emerald-500 to-teal-500 text-white hover:from-emerald-600 hover:to-teal-600 transition-all"
                        >
                            {t('open')}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
