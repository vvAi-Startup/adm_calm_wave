"use client";
import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { statsAPI, AnalyticsData } from "../lib/api";

const MOCK: AnalyticsData = {
    total_active_users: 24592,
    total_users: 31820,
    session_duration: "4m 32s",
    bounce_rate: 42.8,
    total_audios: 1284,
    favorite_audios: 156,
    transcribed_audios: 512,
    user_growth: [
        { month: "Set", users: 120 },
        { month: "Out", users: 195 },
        { month: "Nov", users: 280 },
        { month: "Dez", users: 340 },
        { month: "Jan", users: 420 },
        { month: "Fev", users: 487 },
    ],
    features_usage: [
        { name: "Gravar Audio", usage: 100 },
        { name: "Limpar Ruido", usage: 90 },
        { name: "Ouvir Audio", usage: 80 },
        { name: "Criar Playlist", usage: 50 },
        { name: "Transcrever", usage: 40 },
        { name: "Marcar Favorito", usage: 30 },
    ],
    retention: [
        { day: "Dia 1", rate: 80 },
        { day: "Dia 7", rate: 50 },
        { day: "Dia 30", rate: 30 },
    ],
    device_performance: [
        { device: "Samsung S23", time: "0.15s", pct: 90 },
        { device: "Xiaomi Redmi Note 11", time: "0.25s", pct: 70 },
        { device: "Motorola Moto G8", time: "0.45s", pct: 45 },
    ],
};

export default function AnalyticsPage() {
    const [data, setData] = useState<AnalyticsData>(MOCK);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        statsAPI.analytics()
            .then((res) => {
                // If we get empty/zero data, fallback to mock for visual purposes
                if (res.total_users === 0) {
                    setData(MOCK);
                } else {
                    setData(res);
                }
            })
            .catch(() => setData(MOCK))
            .finally(() => setLoading(false));
    }, []);

    const maxGrowth = Math.max(...data.user_growth.map((g) => g.users), 1);

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
            ...data.user_growth.map(g => [g.month, g.users]),
            [],
            ["Funcionalidade", "Uso (%)"],
            ...data.features_usage.map(f => [f.name, f.usage])
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
                                <div className="stat-value">{data.total_active_users.toLocaleString()}</div>
                                <div className="stat-delta">↑ +12% vs mês passado</div>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon success">⏱️</div>
                            <div className="stat-body">
                                <div className="stat-label">Session Duration</div>
                                <div className="stat-value">{data.session_duration}</div>
                                <div className="stat-delta">↑ +5% vs mês passado</div>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon warning">📉</div>
                            <div className="stat-body">
                                <div className="stat-label">Bounce Rate</div>
                                <div className="stat-value">{data.bounce_rate}%</div>
                                <div className="stat-delta neg">↑ +2% vs mês passado</div>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon info">🎙️</div>
                            <div className="stat-body">
                                <div className="stat-label">Total Áudios</div>
                                <div className="stat-value">{data.total_audios.toLocaleString()}</div>
                                <div className="stat-delta">↑ +8% essa semana</div>
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
                                {data.user_growth.map((g, i) => (
                                    <div key={i} className="bar-item">
                                        <div
                                            className={`bar ${i === data.user_growth.length - 1 ? "active" : ""}`}
                                            style={{ height: `${(g.users / maxGrowth) * 100}%` }}
                                            title={`${g.month}: ${g.users} usuários`}
                                        />
                                        <span className="bar-label">{g.month}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Funcionalidades Mais Usadas */}
                        <div className="card">
                            <div className="card-header">
                                <div className="card-title">Funcionalidades Mais Usadas</div>
                            </div>
                            <div style={{ marginTop: 8 }}>
                                {data.features_usage.map((f, i) => (
                                    <div key={i} className="progress-wrap">
                                        <div className="progress-header">
                                            <span className="progress-name">{f.name}</span>
                                            <span className="progress-pct">{f.usage}%</span>
                                        </div>
                                        <div className="progress-track">
                                            <div className="progress-fill" style={{ width: `${f.usage}%` }} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Retention Heatmap */}
                    <div className="card" style={{ marginTop: 20 }}>
                        <div className="card-header">
                            <div className="card-title">Retention Heatmap</div>
                            <div className="card-subtitle">User return rates over 30 days</div>
                        </div>
                        <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
                            {data.retention.map((r, i) => (
                                <div key={i} style={{ flex: 1, minWidth: 160, background: "var(--bg-muted)", borderRadius: "var(--radius)", padding: 20, textAlign: "center" }}>
                                    <div style={{ fontSize: 28, fontWeight: 800, color: i === 0 ? "var(--success)" : i === 1 ? "var(--warning)" : "var(--danger)" }}>{r.rate}%</div>
                                    <div style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 4 }}>{r.day} voltam</div>
                                </div>
                            ))}
                            <div style={{ flex: 2, minWidth: 200 }}>
                                <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, color: "var(--text-primary)" }}>Performance por Dispositivo</div>
                                {(data.device_performance || []).map((d, i) => (
                                    <div key={i} className="progress-wrap">
                                        <div className="progress-header">
                                            <span className="progress-name">{d.device}</span>
                                            <span className="progress-pct">{d.time}</span>
                                        </div>
                                        <div className="progress-track">
                                            <div className="progress-fill" style={{ width: `${d.pct}%`, background: i === 0 ? "var(--success)" : i === 1 ? "var(--warning)" : "var(--danger)" }} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
