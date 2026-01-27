"use client";

export default function EmailSettings() {
    return (
        <div className="max-w-2xl space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
                <h3 className="text-lg font-semibold text-slate-800 mb-6">Configuration SMTP</h3>

                <div className="grid grid-cols-1 gap-6">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">Serveur SMTP</label>
                        <input
                            type="text"
                            className="w-full rounded-lg border-slate-300 focus:ring-brand-primary focus:border-brand-primary"
                            placeholder="smtp.office365.com"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">Port</label>
                            <input
                                type="text"
                                className="w-full rounded-lg border-slate-300 focus:ring-brand-primary focus:border-brand-primary"
                                placeholder="587"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">Sécurité</label>
                            <select className="w-full rounded-lg border-slate-300 focus:ring-brand-primary focus:border-brand-primary">
                                <option>STARTTLS</option>
                                <option>SSL/TLS</option>
                                <option>Aucune</option>
                            </select>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">Email expéditeur</label>
                        <input
                            type="email"
                            className="w-full rounded-lg border-slate-300 focus:ring-brand-primary focus:border-brand-primary"
                            placeholder="notifications@bboxl.com"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">Mot de passe d'application</label>
                        <input
                            type="password"
                            className="w-full rounded-lg border-slate-300 focus:ring-brand-primary focus:border-brand-primary"
                            placeholder="••••••••••••••••"
                        />
                    </div>

                    <div className="pt-4 flex items-center justify-between">
                        <button className="text-brand-primary hover:text-brand-secondary text-sm font-medium">
                            Tester la connexion
                        </button>
                        <button className="bg-brand-primary hover:bg-brand-secondary text-white px-6 py-2 rounded-lg font-medium transition-colors">
                            Sauvegarder
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
