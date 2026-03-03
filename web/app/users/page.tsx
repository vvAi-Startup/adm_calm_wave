"use client";
import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { usersAPI, User } from "../lib/api";

const MOCK_USERS: User[] = [
    { id: 1, name: "Ana Souza", email: "ana@calmwave.com", account_type: "premium", active: true, created_at: "2026-01-15T10:00:00Z", last_access: "2026-02-24T18:30:00Z" },
    { id: 2, name: "Bruno Lima", email: "bruno@email.com", account_type: "free", active: true, created_at: "2026-01-28T14:00:00Z", last_access: "2026-02-23T09:15:00Z" },
    { id: 3, name: "Carla Mendes", email: "carla@email.com", account_type: "premium", active: true, created_at: "2026-02-01T08:30:00Z", last_access: "2026-02-24T11:00:00Z" },
    { id: 4, name: "Diego Costa", email: "diego@email.com", account_type: "free", active: false, created_at: "2026-02-10T12:00:00Z", last_access: "2026-02-18T16:45:00Z" },
    { id: 5, name: "Elisa Torres", email: "elisa@email.com", account_type: "admin", active: true, created_at: "2025-12-01T09:00:00Z", last_access: "2026-02-24T19:00:00Z" },
];

export default function UsersPage() {
    const [users, setUsers] = useState<User[]>([]);
    const [total, setTotal] = useState(0);
    const [pages, setPages] = useState(1);
    const [currentPage, setCurrentPage] = useState(1);
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<number | null>(null);

    useEffect(() => {
        setLoading(true);
        usersAPI.list({ page: currentPage })
            .then((res) => { 
                
                    setUsers(res.users); 
                    setTotal(res.total); 
                    setPages(res.pages); 
                
            })
            .catch(() => { setUsers(MOCK_USERS); setTotal(MOCK_USERS.length); setPages(1); })
            .finally(() => setLoading(false));
    }, [currentPage]);

    const filtered = users.filter((u) => u.name.toLowerCase().includes(search.toLowerCase()) || u.email.toLowerCase().includes(search.toLowerCase()));

    const toggleStatus = async (user: User) => {
        setActionLoading(user.id);
        try {
            const res = await usersAPI.update(user.id, { active: !user.active });
            setUsers((prev) => prev.map((u) => u.id === user.id ? res.user : u));
        } catch {
            alert("Erro ao atualizar status do usuário.");
            // Fallback for mock data
            setUsers((prev) => prev.map((u) => u.id === user.id ? { ...u, active: !u.active } : u));
        } finally {
            setActionLoading(null);
        }
    };

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main">
                <Header title="Gerenciamento de Usuários" subtitle="Gerencie contas, permissões e status dos usuários" />
                <div className="page-content">
                    <div className="stats-grid" style={{ gridTemplateColumns: "repeat(4,1fr)" }}>
                        <div className="stat-card"><div className="stat-icon brand">👥</div><div className="stat-body"><div className="stat-label">Total</div><div className="stat-value">{total || MOCK_USERS.length}</div></div></div>
                        <div className="stat-card"><div className="stat-icon success">✅</div><div className="stat-body"><div className="stat-label">Ativos</div><div className="stat-value">{users.filter(u => u.active).length || 4}</div></div></div>
                        <div className="stat-card"><div className="stat-icon warning">⭐</div><div className="stat-body"><div className="stat-label">Premium</div><div className="stat-value">{users.filter(u => u.account_type === "premium").length || 2}</div></div></div>
                        <div className="stat-card"><div className="stat-icon danger">🚫</div><div className="stat-body"><div className="stat-label">Inativos</div><div className="stat-value">{users.filter(u => !u.active).length || 1}</div></div></div>
                    </div>

                    <div className="card">
                        <div className="card-header">
                            <div className="card-title">Usuários</div>
                            <div className="search-bar" style={{ width: 260 }}>
                                <span>🔍</span>
                                <input placeholder="Buscar usuário..." value={search} onChange={(e) => setSearch(e.target.value)} />
                            </div>
                        </div>
                        <div className="table-wrap">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Usuário</th>
                                        <th>Email</th>
                                        <th>Tipo</th>
                                        <th>Status</th>
                                        <th>Membro desde</th>
                                        <th>Último acesso</th>
                                        <th>Ações</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {loading ? (
                                        <tr><td colSpan={7} style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>Carregando...</td></tr>
                                    ) : filtered.map((user) => (
                                        <tr key={user.id}>
                                            <td>
                                                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                                    <div className="sidebar-avatar" style={{ width: 32, height: 32, fontSize: 13 }}>{user.name.charAt(0)}</div>
                                                    <span style={{ fontWeight: 600 }}>{user.name}</span>
                                                </div>
                                            </td>
                                            <td className="text-muted">{user.email}</td>
                                            <td>
                                                <span className={`badge ${user.account_type === "premium" ? "badge-brand" : user.account_type === "admin" ? "badge-danger" : "badge-muted"}`}>
                                                    {user.account_type}
                                                </span>
                                            </td>
                                            <td><span className={`badge ${user.active ? "badge-success" : "badge-danger"}`}><span className="badge-dot" />{user.active ? "Ativo" : "Inativo"}</span></td>
                                            <td className="text-muted">{new Date(user.created_at).toLocaleDateString("pt-BR")}</td>
                                            <td className="text-muted">{new Date(user.last_access).toLocaleDateString("pt-BR")}</td>
                                            <td>
                                                <div style={{ display: "flex", gap: 6 }}>
                                                    <button 
                                                        className="btn-icon" 
                                                        title={user.active ? "Desativar" : "Ativar"} 
                                                        onClick={() => toggleStatus(user)}
                                                        disabled={actionLoading === user.id}
                                                        style={{ opacity: actionLoading === user.id ? 0.5 : 1 }}
                                                    >
                                                        {actionLoading === user.id ? "⏳" : user.active ? "🚫" : "✅"}
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        
                        {/* Pagination Controls */}
                        {pages > 1 && (
                            <div style={{ display: "flex", justifyContent: "center", gap: 8, padding: 16, borderTop: "1px solid var(--border)" }}>
                                <button 
                                    className="btn btn-secondary btn-sm" 
                                    disabled={currentPage === 1}
                                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                >
                                    Anterior
                                </button>
                                <span style={{ display: "flex", alignItems: "center", fontSize: 14 }}>
                                    Página {currentPage} de {pages}
                                </span>
                                <button 
                                    className="btn btn-secondary btn-sm" 
                                    disabled={currentPage === pages}
                                    onClick={() => setCurrentPage(p => Math.min(pages, p + 1))}
                                >
                                    Próxima
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
