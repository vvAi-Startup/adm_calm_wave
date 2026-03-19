"use client";
import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { statsAPI, AnalyticsData } from "../lib/api";

const EMPTY_DATA: AnalyticsData = {
    total_active_users: 0,
    total_users: 0,
    session_duration: "0m 0s",
    bounce_rate: 0,
    total_audios: 0,
    favorite_audios: 0,
    transcribed_audios: 0,
    user_growth: [],
    features_usage: [],
    retention: [],
    device_performance: [],
};

export default function AnalyticsPage() {
    const [data, setData] = useState<AnalyticsData>(EMPTY_DATA);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        statsAPI.analytics()
            .then((res) => {
                // Removemos o uso de mocks em produção.
                setData(res);
            })
            .catch(() => setData(EMPTY_DATA))
            .finally(() => setLoading(false));
    }, []);

    const maxGrowth = Math.max(...(data.user_growth || []).map((g) => g.users), 1);

    const handleExportCSV = () => {
        const rows = [
            ["Metrica", "Valor"],
            ["Total Active Users", data.total_active_users],
            ["Total Users", data.total_users],
            ["Session Duration", data.session_duration],
            ["Bounce Rate", data.bounce_rate + "%"],
            ["Total Audios", data.total_audios],
            [],
            ["Mes", "Novos Usuarios"],
            ...(data.user_growth || []).map(g => [g.month, g.users]),
            [],
            ["Funcionalidade", "Uso (%)"],
            ...(data.features_usage || []).map(f => [f.name, f.usage])
        ];

        const csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\n");
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `calmwave_analytics_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleExportPDF = () => {
        // Usa o print do navegador estilizado
        window.print();
    };

    if (loading) {
        return (
            <div className="app-layout">
                <Sidebar />
                <main className="app-main">
                    <Header title="Analytics Avançado" subtitle="Carregando estatísticas da API..." />
                    <div className="page-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 400 }}>
                        <div style={{ color: "var(--text-muted)" }}>⏳ Obtendo dados em tempo real...</div>
                    </div>
                </main>
            </div>
        );
    }

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main print-main">
                <Header title="Analytics Avançado" subtitle="Real-time metrics and performance data insights" />
                <div className="page-content" id="printable-area">
                    <div className="hide-on-print" style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginBottom: 20 }}>
                        <button className="btn btn-secondary" onClick={handleExportCSV}>📊 Exportar CSV</button>
                        <button className="btn btn-primary" onClick={handleExportPDF}>📄 Exportar PDF</button>
                    </div>
                    {/* Stat Cards */}
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-icon brand">👥</div>
                            <div className="stat-body">
                                <div className="stat-label">Total Active Users</div>
                                <div className="stat-value">{data.total_active_users?.toLocaleString() || 0}</div>
                                <div className="stat-delta text-muted">— calculando</div>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon success">⏱️</div>
                            <div className="stat-body">
                                <div className="stat-label">Session Duration</div>
                                <div className="stat-value">{data.session_duration || "0m 0s"}</div>
                                <div className="stat-delta text-muted">— calculando</div>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon warning">📉</div>
                            <div className="stat-body">
                                <div className="stat-label">Bounce Rate</div>
                                <div className="stat-value">{data.bounce_rate || 0}%</div>
                                <div className="stat-delta text-muted">— calculando</div>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon info">🎙️</div>
                            <div className="stat-body">
                                <div className="stat-label">Total Áudios</div>
                                <div className="stat-value">{data.total_audios?.toLocaleString() || 0}</div>
                                <div className="stat-delta text-muted">— calculando</div>
                            </div>
                        </div>
                    </div>

                    <div className="grid-2">
                        {/* Crescimento de Usuários */}
                        <div className="card">
                            <div className="card-header">
                                <div className="card-title">User Growth Trends</div>
                                <span className="badge badge-brand">Últimos 6 meses</span>
                            </div>
                            <div className="bar-chart">
                                {data.user_growth && data.user_growth.length > 0 ? (
                                    data.user_growth.map((g, i) => (
                                        <div key={i} className="bar-item">
                                            <div
                                                className={`bar ${i === data.user_growth.length - 1 ? "active" : ""}`}
                                                style={{ height: `${(g.users / maxGrowth) * 100}%` }}
                                                title={`${g.month}: ${g.users} usuários`}
                                            />
                                            <span className="bar-label">{g.month}</span>
                                        </div>
                                    ))
                                ) : (
                                    <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Sem dados de crescimento para exibir.</div>
                                )}
                            </div>
                        </div>

                        {/* Funcionalidades Mais Usadas */}
                        <div className="card">
                            <div className="card-header">
                                <div className="card-title">Funcionalidades Mais Usadas</div>
                            </div>
                            <div style={{ marginTop: 8 }}>
                                {data.features_usage && data.features_usage.length > 0 ? (
                                    data.features_usage.map((f, i) => (
                                        <div key={i} className="progress-wrap">
                                            <div className="progress-header">
                                                <span className="progress-name">{f.name}</span>
                                                <span className="progress-pct">{f.usage}%</span>
                                            </div>
                                            <div className="progress-track">
                                                <div className="progress-fill" style={{ width: `${f.usage}%` }} />
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Métricas insuficientes.</div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Retention Heatmap */}
                    <div className="card" style={{ marginTop: 20 }}>
                        <div className="card-header">
                            <div className="card-title">Retention Heatmap</div>
                            <div className="card-subtitle">User return rates over 30 days</div>
                        </div>
                        <div style={{ display: "flex", gap: 20, flexWrap: "wrap", alignItems: 'center' }}>
                            {data.retention && data.retention.length > 0 ? (
                                data.retention.map((r, i) => (
                                    <div key={i} style={{ flex: 1, minWidth: 160, background: "var(--bg-muted)", borderRadius: "var(--radius)", padding: 20, textAlign: "center" }}>
                                        <div style={{ fontSize: 28, fontWeight: 800, color: i === 0 ? "var(--success)" : i === 1 ? "var(--warning)" : "var(--danger)" }}>{r.rate}%</div>
                                        <div style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 4 }}>{r.day} voltam</div>
                                    </div>
                                ))
                            ) : (
                                <div style={{ flex: 1, minWidth: 160, background: "var(--card-bg)", color: "var(--text-muted)", borderRadius: "var(--radius)", padding: 20, textAlign: "center" }}>
                                    <div style={{ fontSize: 14 }}>Coletando dados de retenção (Dia 1 a Dia 30)...</div>
                                </div>
                            )}

                            <div style={{ flex: 2, minWidth: 200, paddingLeft: 20, borderLeft: "1px solid var(--border)" }}>
                                <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, color: "var(--text-primary)" }}>Performance por Dispositivo</div>
                                {data.device_performance && data.device_performance.length > 0 ? (
                                    data.device_performance.map((d, i) => (
                                        <div key={i} className="progress-wrap">
                                            <div className="progress-header">
                                                <span className="progress-name">{d.device}</span>
                                                <span className="progress-pct">{d.time}</span>
                                            </div>
                                            <div className="progress-track">
                                                <div className="progress-fill" style={{ width: `${d.pct}%`, background: i === 0 ? "var(--success)" : i === 1 ? "var(--warning)" : "var(--danger)" }} />
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <div style={{ fontSize: 13, color: "var(--text-muted)" }}>Aguardando sessões de usuários para calcular performance do lado do cliente.</div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
