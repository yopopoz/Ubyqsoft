'use client';

import React, { useState, useCallback, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { ApiError } from '@/services/api';
import { useTranslations } from 'next-intl';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

// Types
interface ImportPreviewRow {
    row_number: number;
    reference: string | null;
    customer: string | null;
    order_number: string | null;
    planned_etd: string | null;
    status: 'new' | 'update' | 'error';
    error: string | null;
}

interface ImportPreviewResult {
    rows: ImportPreviewRow[];
    columns_found: string[];
    total_rows: number;
    new_count: number;
    update_count: number;
    error_count: number;
}

interface ImportResult {
    created: number;
    updated: number;
    skipped: number;
    errors: { row: number; reference: string | null; error: string }[];
    total_processed: number;
}

type ImportMode = 'create_only' | 'update_or_create';

interface ExcelImportModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess?: () => void;
}

export default function ExcelImportModal({ isOpen, onClose, onSuccess }: ExcelImportModalProps) {
    const { token } = useAuth();
    const t = useTranslations('Import');
    const fileInputRef = useRef<HTMLInputElement>(null);

    // State
    const [file, setFile] = useState<File | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [preview, setPreview] = useState<ImportPreviewResult | null>(null);
    const [importResult, setImportResult] = useState<ImportResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [mode, setMode] = useState<ImportMode>('update_or_create');
    const [step, setStep] = useState<'upload' | 'preview' | 'result'>('upload');

    // Reset state
    const reset = useCallback(() => {
        setFile(null);
        setPreview(null);
        setImportResult(null);
        setError(null);
        setStep('upload');
        setIsLoading(false);
    }, []);

    // Handle close
    const handleClose = () => {
        reset();
        onClose();
    };

    // Drag handlers
    const handleDragEnter = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    }, []);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const files = e.dataTransfer?.files;
        if (files && files.length > 0) {
            const droppedFile = files[0];
            if (droppedFile.name.endsWith('.xlsx') || droppedFile.name.endsWith('.xls')) {
                setFile(droppedFile);
                setError(null);
            } else {
                setError(t('invalidFormat'));
            }
        }
    }, []);

    // File input handler
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            const selectedFile = files[0];
            if (selectedFile.name.endsWith('.xlsx') || selectedFile.name.endsWith('.xls')) {
                setFile(selectedFile);
                setError(null);
            } else {
                setError(t('invalidFormat'));
            }
        }
    };

    // Preview file
    const handlePreview = async () => {
        if (!file || !token) return;

        setIsLoading(true);
        setError(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API_BASE}/shipments/import/preview`, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || t('errors.preview'));
            }

            const data: ImportPreviewResult = await response.json();
            setPreview(data);
            setStep('preview');
        } catch (err) {
            setError(err instanceof Error ? err.message : t('errors.unknown'));
        } finally {
            setIsLoading(false);
        }
    };

    // Execute import
    const handleImport = async () => {
        if (!file || !token) return;

        setIsLoading(true);
        setError(null);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('mode', mode);

        try {
            const response = await fetch(`${API_BASE}/shipments/import`, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || t('errors.import'));
            }

            const data: ImportResult = await response.json();
            setImportResult(data);
            setStep('result');
            if (onSuccess) onSuccess();
        } catch (err) {
            setError(err instanceof Error ? err.message : t('errors.unknown'));
        } finally {
            setIsLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div
                className="relative w-full max-w-4xl max-h-[90vh] bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl shadow-2xl border border-slate-700/50 overflow-hidden"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700/50 bg-slate-800/50">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-emerald-500/20">
                            <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                            </svg>
                        </div>
                        <h2 className="text-xl font-semibold text-white">{t('title')}</h2>
                    </div>
                    <button
                        onClick={handleClose}
                        className="p-2 rounded-lg hover:bg-slate-700/50 transition-colors"
                    >
                        <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
                    {/* Error message */}
                    {error && (
                        <div className="mb-4 p-4 rounded-lg bg-red-500/20 border border-red-500/30">
                            <p className="text-red-400 text-sm">{error}</p>
                        </div>
                    )}

                    {/* Step 1: Upload */}
                    {step === 'upload' && (
                        <div className="space-y-6">
                            {/* Dropzone */}
                            <div
                                onDragEnter={handleDragEnter}
                                onDragLeave={handleDragLeave}
                                onDragOver={handleDragOver}
                                onDrop={handleDrop}
                                onClick={() => fileInputRef.current?.click()}
                                className={`
                                    relative p-8 border-2 border-dashed rounded-xl cursor-pointer transition-all duration-300
                                    ${isDragging
                                        ? 'border-emerald-400 bg-emerald-500/10'
                                        : file
                                            ? 'border-emerald-500/50 bg-emerald-500/5'
                                            : 'border-slate-600 hover:border-slate-500 bg-slate-800/30'}
                                `}
                            >
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".xlsx,.xls"
                                    onChange={handleFileChange}
                                    className="hidden"
                                />

                                <div className="flex flex-col items-center gap-4">
                                    {file ? (
                                        <>
                                            <div className="p-4 rounded-full bg-emerald-500/20">
                                                <svg className="w-8 h-8 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                </svg>
                                            </div>
                                            <div className="text-center">
                                                <p className="text-white font-medium">{file.name}</p>
                                                <p className="text-slate-400 text-sm mt-1">
                                                    {(file.size / 1024).toFixed(1)} KB
                                                </p>
                                            </div>
                                        </>
                                    ) : (
                                        <>
                                            <div className="p-4 rounded-full bg-slate-700/50">
                                                <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                                </svg>
                                            </div>
                                            <div className="text-center">
                                                <p className="text-white font-medium">
                                                    {t('dragDrop')}
                                                </p>
                                                <p className="text-slate-400 text-sm mt-1">
                                                    {t('clickSelect')}
                                                </p>
                                            </div>
                                        </>
                                    )}
                                </div>
                            </div>

                            {/* Mode selector */}
                            <div className="space-y-3">
                                <label className="text-sm text-slate-300 font-medium">{t('mode')}</label>
                                <div className="grid grid-cols-2 gap-4">
                                    <button
                                        onClick={() => setMode('update_or_create')}
                                        className={`p-4 rounded-xl border transition-all ${mode === 'update_or_create'
                                            ? 'border-emerald-500 bg-emerald-500/10'
                                            : 'border-slate-600 hover:border-slate-500 bg-slate-800/30'
                                            }`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className={`w-4 h-4 rounded-full border-2 ${mode === 'update_or_create' ? 'border-emerald-500 bg-emerald-500' : 'border-slate-500'
                                                }`} />
                                            <div className="text-left">
                                                <p className="text-white font-medium">{t('updateOrCreate')}</p>
                                                <p className="text-slate-400 text-xs mt-1">
                                                    {t('updateOrCreateDesc')}
                                                </p>
                                            </div>
                                        </div>
                                    </button>
                                    <button
                                        onClick={() => setMode('create_only')}
                                        className={`p-4 rounded-xl border transition-all ${mode === 'create_only'
                                            ? 'border-blue-500 bg-blue-500/10'
                                            : 'border-slate-600 hover:border-slate-500 bg-slate-800/30'
                                            }`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className={`w-4 h-4 rounded-full border-2 ${mode === 'create_only' ? 'border-blue-500 bg-blue-500' : 'border-slate-500'
                                                }`} />
                                            <div className="text-left">
                                                <p className="text-white font-medium">{t('createOnly')}</p>
                                                <p className="text-slate-400 text-xs mt-1">
                                                    {t('createOnlyDesc')}
                                                </p>
                                            </div>
                                        </div>
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Step 2: Preview */}
                    {step === 'preview' && preview && (
                        <div className="space-y-4">
                            {/* Stats */}
                            <div className="grid grid-cols-3 gap-4">
                                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
                                    <p className="text-emerald-400 text-2xl font-bold">{preview.new_count}</p>
                                    <p className="text-emerald-300/70 text-sm">{t('stats.new')}</p>
                                </div>
                                <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/30">
                                    <p className="text-blue-400 text-2xl font-bold">{preview.update_count}</p>
                                    <p className="text-blue-300/70 text-sm">{t('stats.updates')}</p>
                                </div>
                                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30">
                                    <p className="text-red-400 text-2xl font-bold">{preview.error_count}</p>
                                    <p className="text-red-300/70 text-sm">{t('stats.errors')}</p>
                                </div>
                            </div>

                            {/* Table */}
                            <div className="rounded-xl border border-slate-700/50 overflow-hidden">
                                <div className="overflow-x-auto max-h-[400px]">
                                    <table className="w-full text-sm">
                                        <thead className="bg-slate-800/80 sticky top-0">
                                            <tr>
                                                <th className="px-4 py-3 text-left text-slate-300 font-medium">{t('table.row')}</th>
                                                <th className="px-4 py-3 text-left text-slate-300 font-medium">{t('table.reference')}</th>
                                                <th className="px-4 py-3 text-left text-slate-300 font-medium">{t('table.customer')}</th>
                                                <th className="px-4 py-3 text-left text-slate-300 font-medium">{t('table.order')}</th>
                                                <th className="px-4 py-3 text-left text-slate-300 font-medium">{t('table.status')}</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-700/50">
                                            {preview.rows.slice(0, 50).map((row) => (
                                                <tr key={row.row_number} className="hover:bg-slate-800/30">
                                                    <td className="px-4 py-3 text-slate-400">{row.row_number}</td>
                                                    <td className="px-4 py-3 text-white font-mono text-xs">{row.reference || '-'}</td>
                                                    <td className="px-4 py-3 text-slate-300">{row.customer || '-'}</td>
                                                    <td className="px-4 py-3 text-slate-300">{row.order_number || '-'}</td>
                                                    <td className="px-4 py-3">
                                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${row.status === 'new'
                                                            ? 'bg-emerald-500/20 text-emerald-400'
                                                            : row.status === 'update'
                                                                ? 'bg-blue-500/20 text-blue-400'
                                                                : 'bg-red-500/20 text-red-400'
                                                            }`}>
                                                            {row.status === 'new' ? t('status.new') : row.status === 'update' ? t('status.update') : t('status.error')}
                                                        </span>
                                                        {row.error && (
                                                            <p className="text-red-400 text-xs mt-1">{row.error}</p>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                                {preview.total_rows > 50 && (
                                    <div className="px-4 py-2 bg-slate-800/50 text-slate-400 text-sm text-center">
                                        {t('table.showingRows', { total: preview.total_rows })}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Step 3: Result */}
                    {step === 'result' && importResult && (
                        <div className="space-y-6">
                            <div className="text-center py-6">
                                <div className="inline-flex p-4 rounded-full bg-emerald-500/20 mb-4">
                                    <svg className="w-12 h-12 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                <h3 className="text-xl font-semibold text-white">{t('success.title')}</h3>
                                <p className="text-slate-400 mt-2">{t('success.processed', { count: importResult.total_processed })}</p>
                            </div>

                            {/* Stats */}
                            <div className="grid grid-cols-4 gap-4">
                                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-center">
                                    <p className="text-emerald-400 text-2xl font-bold">{importResult.created}</p>
                                    <p className="text-emerald-300/70 text-sm">{t('stats.new')}</p>
                                </div>
                                <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/30 text-center">
                                    <p className="text-blue-400 text-2xl font-bold">{importResult.updated}</p>
                                    <p className="text-blue-300/70 text-sm">{t('stats.updates')}</p>
                                </div>
                                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-center">
                                    <p className="text-amber-400 text-2xl font-bold">{importResult.skipped}</p>
                                    <p className="text-amber-300/70 text-sm">{t('stats.skipped')}</p>
                                </div>
                                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-center">
                                    <p className="text-red-400 text-2xl font-bold">{importResult.errors.length}</p>
                                    <p className="text-red-300/70 text-sm">{t('stats.errors')}</p>
                                </div>
                            </div>

                            {/* Errors list */}
                            {importResult.errors.length > 0 && (
                                <div className="rounded-xl border border-red-500/30 overflow-hidden">
                                    <div className="px-4 py-3 bg-red-500/10 border-b border-red-500/30">
                                        <h4 className="text-red-400 font-medium">{t('errors.title')}</h4>
                                    </div>
                                    <div className="max-h-[200px] overflow-y-auto">
                                        {importResult.errors.map((err, idx) => (
                                            <div key={idx} className="px-4 py-2 border-b border-slate-700/30 last:border-0">
                                                <span className="text-slate-400">Ligne {err.row}</span>
                                                {err.reference && <span className="text-slate-500 mx-2">|</span>}
                                                {err.reference && <span className="text-slate-300 font-mono text-xs">{err.reference}</span>}
                                                <p className="text-red-400 text-sm mt-1">{err.error}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between px-6 py-4 border-t border-slate-700/50 bg-slate-800/50">
                    {step === 'upload' && (
                        <>
                            <button
                                onClick={handleClose}
                                className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
                            >
                                {t('buttons.cancel')}
                            </button>
                            <button
                                onClick={handlePreview}
                                disabled={!file || isLoading}
                                className={`px-6 py-2.5 rounded-lg font-medium transition-all ${file && !isLoading
                                    ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white hover:from-emerald-600 hover:to-teal-600'
                                    : 'bg-slate-700 text-slate-400 cursor-not-allowed'
                                    }`}
                            >
                                {isLoading ? (
                                    <span className="flex items-center gap-2">
                                        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                        </svg>
                                        {t('buttons.loading')}
                                    </span>
                                ) : t('buttons.preview')}
                            </button>
                        </>
                    )}

                    {step === 'preview' && (
                        <>
                            <button
                                onClick={() => setStep('upload')}
                                className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
                            >
                                ← {t('buttons.back')}
                            </button>
                            <button
                                onClick={handleImport}
                                disabled={isLoading || (preview?.error_count === preview?.total_rows)}
                                className={`px-6 py-2.5 rounded-lg font-medium transition-all ${!isLoading && preview?.error_count !== preview?.total_rows
                                    ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white hover:from-emerald-600 hover:to-teal-600'
                                    : 'bg-slate-700 text-slate-400 cursor-not-allowed'
                                    }`}
                            >
                                {isLoading ? (
                                    <span className="flex items-center gap-2">
                                        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                        </svg>
                                        {t('loadingData')}
                                    </span>
                                ) : t('buttons.confirm')}
                            </button>
                        </>
                    )}

                    {step === 'result' && (
                        <>
                            <button
                                onClick={reset}
                                className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
                            >
                                {t('buttons.newImport')}
                            </button>
                            <button
                                onClick={handleClose}
                                className="px-6 py-2.5 rounded-lg font-medium bg-gradient-to-r from-emerald-500 to-teal-500 text-white hover:from-emerald-600 hover:to-teal-600 transition-all"
                            >
                                {t('buttons.close')}
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
