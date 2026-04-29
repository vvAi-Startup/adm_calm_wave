"use client";
import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { eventsAPI, Event } from "../lib/api";



const levelBadge: Record<string, string> = {
    info: "badge-info",
    warn: "badge-warning",
    error: "badge-danger",
};

const levelIcon: Record<string, string> = { info: "ℹ️", warn: "⚠️", error: "❌" };

export default function LogsPage() {
    const [events, setEvents] = useState<Event[]>([]);
    const [search, setSearch] = useState("");
    const [levelFilter, setLevelFilter] = useState("all");
    const [loading, setLoading] = useState(true);

    const fetchEvents = () => {
        setLoading(true);
        eventsAPI.list()
            .then((res) => {
                
                    setEvents(res.events);
                
            })
            .catch((err) => { console.error(err); setEvents([]); })
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        /* eslint-disable react-hooks/set-state-in-effect */
        fetchEvents();
        
        // Auto-refresh every 10 seconds
        const interval = setInterval(fetchEvents, 10000);
        return () => clearInterval(interval);
    }, []);

    const filtered = events.filter((e) => {
        const matchSearch = e.event_type.toLowerCase().includes(search.toLowerCase()) || (e.screen || "").includes(search.toLowerCase());
        const matchLevel = levelFilter === "all" || e.level === levelFilter;
        return matchSearch && matchLevel;
    });

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main">
                <Header title="Logs do Sistema" subtitle="Auditorias, erros e eventos em tempo real" />
                <div className="page-content">
                    <div className="stats-grid" style={{ gridTemplateColumns: "repeat(4,1fr)" }}>
                        <div className="stat-card"><div className="stat-icon info">ℹ️</div><div className="stat-body"><div className="stat-label">Info</div><div className="stat-value">{events.filter(e => e.level === "info").length}</div></div></div>
                        <div className="stat-card"><div className="stat-icon warning">⚠️</div><div className="stat-body"><div className="stat-label">Warnings</div><div className="stat-value">{events.filter(e => e.level === "warn").length}</div></div></div>
                        <div className="stat-card"><div className="stat-icon danger">❌</div><div className="stat-body"><div className="stat-label">Errors</div><div className="stat-value">{events.filter(e => e.level === "error").length}</div></div></div>
                        <div className="stat-card"><div className="stat-icon brand">📋</div><div className="stat-body"><div className="stat-label">Total</div><div className="stat-value">{events.length}</div></div></div>
                    </div>

                    <div className="card">
                        <div className="card-header">
                            <div className="card-title">Logs de Eventos</div>
                            <div className="filters-bar" style={{ margin: 0 }}>
                                <div className="search-bar" style={{ width: 220 }}>
                                    <span>🔍</span>
                                    <input placeholder="Buscar evento..." value={search} onChange={(e) => setSearch(e.target.value)} />
                                </div>
                                <select className="select" style={{ width: "auto" }} value={levelFilter} onChange={(e) => setLevelFilter(e.target.value)}>
                                    <option value="all">Todos</option>
                                    <option value="info">Info</option>
                                    <option value="warn">Warning</option>
                                    <option value="error">Error</option>
                                </select>
                                <button className="btn btn-secondary btn-sm" onClick={fetchEvents}>🔄 Atualizar</button>
                            </div>
                        </div>

                        <div className="table-wrap">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Nível</th>
                                        <th>Evento</th>
                                        <th>Tela/Módulo</th>
                                        <th>Detalhes</th>
                                        <th>Data/Hora</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {loading && events.length === 0 ? (
                                        <tr><td colSpan={5} style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>Carregando...</td></tr>
                                    ) : filtered.length === 0 ? (
                                        <tr><td colSpan={5}><div className="empty-state"><div className="empty-icon">📋</div><div className="empty-title">Nenhum log encontrado</div></div></td></tr>
                                    ) : filtered.map((e) => (
                                        <tr key={e.id}>
                                            <td><span className={`badge ${levelBadge[e.level] || "badge-muted"}`}>{levelIcon[e.level]} {e.level}</span></td>
                                            <td style={{ fontWeight: 600, fontFamily: "monospace", fontSize: 13 }}>{e.event_type}</td>
                                            <td><span className="badge badge-muted">{e.screen || "system"}</span></td>
                                            <td style={{ maxWidth: 350 }}>
                                                <pre style={{ 
                                                    fontSize: 11, 
                                                    background: "var(--bg-muted)", 
                                                    padding: "6px 10px", 
                                                    borderRadius: 6, 
                                                    margin: 0,
                                                    whiteSpace: "pre-wrap",
                                                    wordBreak: "break-word",
                                                    maxHeight: 80,
                                                    overflowY: "auto",
                                                    border: "1px solid var(--border)"
                                                }}>
                                                    {e.details_json ? JSON.stringify(JSON.parse(e.details_json), null, 2) : "—"}
                                                </pre>
                                            </td>
                                            <td className="text-muted" style={{ fontVariantNumeric: "tabular-nums", fontSize: 13 }}>
                                                {new Date(e.created_at).toLocaleString("pt-BR")}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
