"use client";
import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { usersAPI, User } from "../lib/api";

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
            .catch(() => { 
                setUsers([]); 
                setTotal(0); 
                setPages(1); 
            })
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
        } finally {
            setActionLoading(null);
        }
    };

    const changeRole = async (user: User, newRole: string) => {
        setActionLoading(user.id);
        try {
            const res = await usersAPI.update(user.id, { role: newRole });
            setUsers((prev) => prev.map((u) => u.id === user.id ? res.user : u));
        } catch {
            alert("Erro ou permissao negada para alterar o papel.");
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
                        <div className="stat-card"><div className="stat-icon brand">👥</div><div className="stat-body"><div className="stat-label">Total Cadastrados</div><div className="stat-value">{total}</div></div></div>
                        <div className="stat-card"><div className="stat-icon success">✅</div><div className="stat-body"><div className="stat-label">Ativos</div><div className="stat-value">{users.filter(u => u.active).length}</div></div></div>
                        <div className="stat-card"><div className="stat-icon warning">⭐</div><div className="stat-body"><div className="stat-label">Premium</div><div className="stat-value">{users.filter(u => u.account_type === "premium").length}</div></div></div>
                        <div className="stat-card"><div className="stat-icon danger">🚫</div><div className="stat-body"><div className="stat-label">Inativos</div><div className="stat-value">{users.filter(u => !u.active).length}</div></div></div>
                    </div>

                    <div className="card">
                        <div className="card-header">
                            <div className="card-title">Usuários</div>
                            <div className="search-bar" style={{ width: 260 }}>
                                <span>🔍</span>
                                <input placeholder="Buscar usuário..." value={search} onChange={(e) => setSearch(e.target.value)} disabled={loading} />
                            </div>
                        </div>
                        <div className="table-wrap">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Usuário</th>
                                        <th>Email</th>
                                        <th>Plano</th>
                                        <th>Papel</th>
                                        <th>Status</th>
                                        <th>Membro desde</th>
                                        <th>Último acesso</th>
                                        <th>Ações</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {loading ? (
                                        <tr><td colSpan={8} style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>Carregando dados da API...</td></tr>
                                    ) : filtered.length === 0 ? (
                                        <tr><td colSpan={8} style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>Nenhum usuário encontrado no sistema.</td></tr>
                                    ) : filtered.map((user) => (
                                        <tr key={user.id}>
                                            <td>
                                                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                                    <div className="sidebar-avatar" style={{ width: 32, height: 32, fontSize: 13 }}>{user.name?.charAt(0) || '?'}</div>
                                                    <span style={{ fontWeight: 600 }}>{user.name || 'Sem nome'}</span>
                                                </div>
                                            </td>
                                            <td className="text-muted">{user.email || 'N/A'}</td>
                                            <td>
                                                <span className={`badge ${user.account_type === "premium" ? "badge-brand" : "badge-muted"}`}>
                                                    {user.account_type || 'free'}
                                                </span>
                                            </td>
                                            <td>
                                                <select
                                                    value={user.role || "user"}
                                                    onChange={(e) => changeRole(user, e.target.value)}
                                                    disabled={actionLoading === user.id}
                                                    style={{ padding: "4px 8px", borderRadius: "6px", border: "1px solid var(--border)", background: "var(--card-bg)" }}
                                                >
                                                    <option value="user">User</option>
                                                    <option value="admin">Admin</option>
                                                    <option value="super_admin">Super</option>
                                                </select>
                                            </td>
                                            <td><span className={`badge ${user.active ? "badge-success" : "badge-danger"}`}><span className="badge-dot" />{user.active ? "Ativo" : "Inativo"}</span></td>
                                            <td className="text-muted">{user.created_at ? new Date(user.created_at).toLocaleDateString("pt-BR") : "N/A"}</td>
                                            <td className="text-muted">{user.last_access ? new Date(user.last_access).toLocaleDateString("pt-BR") : "N/A"}</td>
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
