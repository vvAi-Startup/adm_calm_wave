"use client";
import { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import Header from "../../components/Header";

interface AuditLog {
    id: number;
    user_id: number | null;
    event_type: string;
    level: string;
    screen: string;
    details_json: string;
    created_at: string;
}

export default function AuditLogsPage() {
    const [logs, setLogs] = useState<AuditLog[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem("calmwave_token");
        fetch("http://localhost:5000/api/admin/audit-logs", {
            headers: { Authorization: `Bearer ${token}` }
        })
            .then(res => res.json())
            .then(data => {
                if (data.logs) {
                    setLogs(data.logs);
                }
            })
            .finally(() => setLoading(false));
    }, []);

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main">
                <Header title="Logs de Auditoria" subtitle="Rastreio restrito para Super Administradores" />
                <div className="page-content">
                    <div className="card">
                        <div className="card-header">
                            <div className="card-title">Eventos Administrativos (Segurança)</div>
                        </div>
                        <div className="table-wrap">
                            <table>
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Data/Hora</th>
                                        <th>Ação Disparada</th>
                                        <th>Origem Tela</th>
                                        <th>Severidade</th>
                                        <th>Assinatura (JSON)</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {loading ? (
                                        <tr><td colSpan={6} style={{ textAlign: "center", padding: 32 }}>Carregando auditoria...</td></tr>
                                    ) : logs.length === 0 ? (
                                        <tr><td colSpan={6} style={{ textAlign: "center", padding: 32 }}>Nenhum log encontrado.</td></tr>
                                    ) : logs.map(log => (
                                        <tr key={log.id}>
                                            <td className="text-muted">#{log.id}</td>
                                            <td className="text-muted">{new Date(log.created_at).toLocaleString()}</td>
                                            <td style={{ fontWeight: 500 }}>{log.event_type}</td>
                                            <td><span className="badge badge-muted">{log.screen}</span></td>
                                            <td>
                                                <span className={`badge ${log.level === 'warn' ? 'badge-warning' : log.level === 'error' ? 'badge-danger' : 'badge-success'}`}>
                                                    {log.level.toUpperCase()}
                                                </span>
                                            </td>
                                            <td>
                                                <pre style={{ margin: 0, padding: "8px", background: "var(--bg-default)", borderRadius: "4px", fontSize: "11px", whiteSpace: "pre-wrap" }}>
                                                    {log.details_json}
                                                </pre>
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
