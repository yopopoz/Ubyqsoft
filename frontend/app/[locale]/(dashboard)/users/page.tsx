"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";

interface User {
    id: number;
    email: string;
    name: string;
    role: string;
    created_at: string;
}

export default function UsersPage() {
    const { token, isAdmin } = useAuth();
    const router = useRouter();
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);

    // Form state
    const [newUser, setNewUser] = useState({
        email: "",
        name: "",
        password: "",
        role: "client"
    });
    const [creating, setCreating] = useState(false);
    const [error, setError] = useState("");
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    useEffect(() => {
        if (!isAdmin) {
            router.push("/");
            return;
        }
        fetchUsers();
    }, [isAdmin, router]);

    const fetchUsers = async () => {
        try {
            const res = await fetch(`${API_BASE}/auth/users`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setUsers(data);
            }
        } catch (e) {
            console.error("Failed to fetch users", e);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        setCreating(true);
        setError("");

        try {
            const res = await fetch(`${API_BASE}/auth/register`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(newUser)
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Échec de la création de l'utilisateur");
            }

            setShowCreateModal(false);
            setNewUser({ email: "", name: "", password: "", role: "client" });
            fetchUsers();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setCreating(false);
        }
    };

    const handleDeleteUser = async (userId: number) => {
        if (!confirm("Êtes-vous sûr de vouloir supprimer cet utilisateur ?")) return;

        try {
            const res = await fetch(`${API_BASE}/auth/users/${userId}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            });

            if (res.ok) {
                fetchUsers();
            } else {
                const errData = await res.json();
                alert(errData.detail || "Échec de la suppression de l'utilisateur");
            }
        } catch (e) {
            console.error("Failed to delete user", e);
        }
    };

    const getRoleBadgeColor = (role: string) => {
        switch (role) {
            case "admin":
                return "bg-red-100 text-red-800";
            case "ops":
                return "bg-slate-100 text-slate-700 border-slate-200";
            default:
                return "bg-gray-100 text-gray-800";
        }
    };

    if (!isAdmin) return null;

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-secondary"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6 max-w-5xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Gestion des Utilisateurs</h2>
                    <p className="text-sm text-gray-500 mt-1">Gérez les utilisateurs du système et leurs rôles</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="rounded-lg bg-brand-secondary px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-brand-secondary/20 hover:bg-red-700 transition-all active:scale-95"
                >
                    + Ajouter un utilisateur
                </button>
            </div>

            {/* Users Table */}
            <div className="overflow-hidden rounded-xl border bg-white shadow">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                                Utilisateur
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                                Email
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                                Rôle
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                                Créé le
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                                Actions
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 bg-white">
                        {users.map((user) => (
                            <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                                <td className="whitespace-nowrap px-6 py-4">
                                    <div className="flex items-center">
                                        <div className="h-10 w-10 flex-shrink-0 rounded-xl bg-brand-primary/10 flex items-center justify-center border border-brand-primary/5">
                                            <span className="text-sm font-bold text-brand-primary">
                                                {(user.name || user.email).charAt(0).toUpperCase()}
                                            </span>
                                        </div>
                                        <div className="ml-4">
                                            <div className="text-sm font-medium text-gray-900">
                                                {user.name || "Sans nom"}
                                            </div>
                                        </div>
                                    </div>
                                </td>
                                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                                    {user.email}
                                </td>
                                <td className="whitespace-nowrap px-6 py-4">
                                    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getRoleBadgeColor(user.role)}`}>
                                        {user.role}
                                    </span>
                                </td>
                                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                                    {(mounted && user.created_at) ? new Date(user.created_at).toLocaleDateString("fr-FR") : "--/--/----"}
                                </td>
                                <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                                    <button
                                        onClick={() => handleDeleteUser(user.id)}
                                        className="text-red-600 hover:text-red-900 font-medium"
                                    >
                                        Supprimer
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {users.length === 0 && (
                            <tr>
                                <td colSpan={5} className="px-6 py-8 text-center text-sm text-gray-500">
                                    Aucun utilisateur trouvé.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Create User Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-2xl">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-xl font-bold text-gray-900">Nouvel Utilisateur</h3>
                            <button
                                onClick={() => setShowCreateModal(false)}
                                className="text-gray-400 hover:text-gray-600"
                            >
                                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        <form onSubmit={handleCreateUser} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Nom</label>
                                <input
                                    type="text"
                                    required
                                    value={newUser.name}
                                    onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                                    className="block w-full rounded-lg border border-slate-300 px-4 py-2 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-all"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                                <input
                                    type="email"
                                    required
                                    value={newUser.email}
                                    onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                                    className="block w-full rounded-lg border border-slate-300 px-4 py-2 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-all"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Mot de passe</label>
                                <input
                                    type="password"
                                    required
                                    value={newUser.password}
                                    onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                                    className="block w-full rounded-lg border border-slate-300 px-4 py-2 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-all"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Rôle</label>
                                <select
                                    value={newUser.role}
                                    onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                                    className="block w-full rounded-lg border border-slate-300 px-4 py-2 shadow-sm focus:border-brand-secondary focus:ring-2 focus:ring-brand-secondary/10 transition-all"
                                >
                                    <option value="client">Client (Lecture seule)</option>
                                    <option value="ops">Opérateur (Accès opérationnel)</option>
                                    <option value="admin">Admin (Accès total)</option>
                                </select>
                            </div>

                            {error && (
                                <div className="text-red-600 text-sm bg-red-50 p-3 rounded-lg">
                                    {error}
                                </div>
                            )}

                            <div className="flex justify-end gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setShowCreateModal(false)}
                                    className="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
                                >
                                    Annuler
                                </button>
                                <button
                                    type="submit"
                                    disabled={creating}
                                    className="rounded-lg bg-brand-primary px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50 transition-all shadow-lg active:scale-95"
                                >
                                    {creating ? "Création..." : "Créer l'utilisateur"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
