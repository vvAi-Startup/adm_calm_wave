"use client";
import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { statsAPI } from "../lib/api";

interface Service {
    name: string;
    status: string;
    uptime: string;
    latency: string;
    icon: string;
}

interface Incident {
    date: string;
    title: string;
    severity: string;
    resolved: boolean;
}

interface StatusData {
    overall_status: string;
    services: Service[];
    incidents: Incident[];
    metrics: {
        online_count: number;
        total_count: number;
        avg_latency: string;
        uptime_30d: string;
    };
}

export default function StatusPage() {
    const [data, setData] = useState<StatusData | null>(null);
    const [loading, setLoading] = useState(true);
    const [lastChecked, setLastChecked] = useState<Date>(new Date());

    const fetchStatus = async () => {
        try {
            const res = await statsAPI.status();
            setData(res);
            setLastChecked(new Date());
        } catch (error) {
            console.error("Failed to fetch status", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 15000); // Refresh every 15s
        return () => clearInterval(interval);
    }, []);

    if (loading && !data) {
        return (
            <div className="app-layout">
                <Sidebar />
                <main className="app-main">
                    <Header title="Status do Sistema" subtitle="Monitoramento em tempo real de todos os serviços" />
                    <div className="page-content" style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "50vh" }}>
                        <div className="spinner"></div>
                    </div>
                </main>
            </div>
        );
    }

    const isAllOperational = data?.overall_status === "online";
    const statusColor = isAllOperational ? "var(--success)" : data?.overall_status === "warn" ? "var(--warning)" : "var(--danger)";
    const statusBg = isAllOperational ? "var(--success-bg)" : data?.overall_status === "warn" ? "var(--warning-bg)" : "var(--danger-bg)";
    const statusIcon = isAllOperational ? "✅" : data?.overall_status === "warn" ? "⚠️" : "🔴";
    const statusText = isAllOperational ? "Todos os serviços operacionais" : data?.overall_status === "warn" ? "Alguns serviços com instabilidade" : "Falha crítica em serviços";

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main">
                <Header title="Status do Sistema" subtitle="Monitoramento em tempo real de todos os serviços" />
                <div className="page-content">
                    {/* Overall status */}
                    <div className="card" style={{ marginBottom: 24, background: statusBg, borderColor: statusColor }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                            <span style={{ fontSize: 40 }}>{statusIcon}</span>
                            <div>
                                <div style={{ fontSize: 20, fontWeight: 800, color: statusColor }}>{statusText}</div>
                                <div style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 4 }}>
                                    Última verificação: {lastChecked.toLocaleTimeString()} · Uptime geral: {data?.metrics.uptime_30d}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="stats-grid" style={{ gridTemplateColumns: "repeat(4,1fr)", marginBottom: 24 }}>
                        <div className="stat-card">
                            <div className="stat-icon success">✅</div>
                            <div className="stat-body">
                                <div className="stat-label">Serviços Online</div>
                                <div className="stat-value">{data?.metrics.online_count}/{data?.metrics.total_count}</div>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className={`stat-icon ${data?.incidents.length ? "warning" : "success"}`}>
                                {data?.incidents.length ? "⚠️" : "✅"}
                            </div>
                            <div className="stat-body">
                                <div className="stat-label">Alertas Ativos</div>
                                <div className="stat-value">{data?.incidents.length || 0}</div>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon brand">⚡</div>
                            <div className="stat-body">
                                <div className="stat-label">Latência Média</div>
                                <div className="stat-value">{data?.metrics.avg_latency}</div>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon info">📅</div>
                            <div className="stat-body">
                                <div className="stat-label">Uptime (30d)</div>
                                <div className="stat-value">{data?.metrics.uptime_30d}</div>
                            </div>
                        </div>
                    </div>

                    <div className="grid-2">
                        <div className="card">
                            <div className="card-header"><div className="card-title">Serviços</div></div>
                            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                                {data?.services.map((s, i) => (
                                    <div key={i} className="status-indicator" style={{ justifyContent: "space-between" }}>
                                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                            <span>{s.icon}</span>
                                            <div>
                                                <div style={{ fontWeight: 600, fontSize: 14 }}>{s.name}</div>
                                                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Uptime: {s.uptime}</div>
                                            </div>
                                        </div>
                                        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{s.latency}</span>
                                            <div className={`status-dot ${s.status}`} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="card">
                            <div className="card-header"><div className="card-title">Histórico de Incidentes</div></div>
                            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                                {data?.incidents.length ? (
                                    data.incidents.map((inc, i) => (
                                        <div key={i} style={{ display: "flex", gap: 12, padding: "12px 0", borderBottom: i < data.incidents.length - 1 ? "1px solid var(--border)" : "none" }}>
                                            <span className={`badge ${inc.severity === "danger" ? "badge-danger" : inc.severity === "warn" ? "badge-warning" : "badge-info"}`} style={{ alignSelf: "flex-start" }}>
                                                {inc.severity === "danger" ? "🔴" : inc.severity === "warn" ? "🟡" : "🔵"}
                                            </span>
                                            <div>
                                                <div style={{ fontWeight: 600, fontSize: 14 }}>{inc.title}</div>
                                                <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                                                    {new Date(inc.date).toLocaleDateString("pt-BR")} · {inc.resolved ? <span style={{ color: "var(--success)" }}>✓ Resolvido</span> : "Em andamento"}
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <div className="empty-state" style={{ padding: "16px 0" }}>
                                        <div style={{ fontSize: 13, color: "var(--success)" }}>✅ Sem novos incidentes</div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
