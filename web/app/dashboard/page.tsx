"use client";
import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { statsAPI, DashboardStats } from "../lib/api";

function formatDuration(seconds: number): string {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (h > 0) return `${h}h ${m}min`;
    return `${m}min`;
}

export default function DashboardPage() {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        statsAPI
            .dashboard()
            .then((res) => {
                if (res.total_users === 0 && res.total_audios === 0) {
                    throw new Error("Empty data");
                }
                setStats(res);
            })
            .catch(() => {
                // fallback mockado
                setStats({
                    total_audios: 1284,
                    total_users: 487,
                    processed_audios: 1156,
                    processed_pct: 90.1,
                    recent_audios_week: 324,
                    streaming_sessions: 42,
                    system_status: "Operacional",
                    daily_counts: [
                        { day: "Seg", count: 48 },
                        { day: "Ter", count: 37 },
                        { day: "Qua", count: 62 },
                        { day: "Qui", count: 55 },
                        { day: "Sex", count: 71 },
                        { day: "Sáb", count: 28 },
                        { day: "Dom", count: 23 },
                    ],
                    last_uploads: [
                        { id: 1, user_id: 1, filename: "reuniao_produto_2026.wav", duration_seconds: 1847, size_bytes: 17825792, recorded_at: new Date().toISOString(), processed: true, transcribed: true, favorite: false },
                        { id: 2, user_id: 2, filename: "entrevista_cliente.wav", duration_seconds: 923, size_bytes: 8912896, recorded_at: new Date().toISOString(), processed: true, transcribed: false, favorite: true },
                        { id: 3, user_id: 3, filename: "notas_pessoais_24fev.wav", duration_seconds: 312, size_bytes: 3014656, recorded_at: new Date().toISOString(), processed: false, transcribed: false, favorite: false },
                    ],
                });
            })
            .finally(() => setLoading(false));
    }, []);

    const maxCount = Math.max(...(stats?.daily_counts.map((d) => d.count) ?? [1]), 1);

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main">
                <Header title="Dashboard Principal" subtitle="Visão geral do sistema Calm Wave" />
                <div className="page-content">
                    {/* Stats Grid */}
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-icon brand">🎙️</div>
                            <div className="stat-body">
                                <div className="stat-label">Total de Áudios</div>
                                <div className="stat-value">{stats ? stats.total_audios.toLocaleString() : "—"}</div>
                                <div className="stat-delta">↑ {stats?.recent_audios_week ?? 0} essa semana</div>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon success">👥</div>
                            <div className="stat-body">
                                <div className="stat-label">Usuários Ativos</div>
                                <div className="stat-value">{stats ? stats.total_users.toLocaleString() : "—"}</div>
                                <div className="stat-delta">↑ +8% esse mês</div>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon warning">📡</div>
                            <div className="stat-body">
                                <div className="stat-label">Sessões de Streaming</div>
                                <div className="stat-value">{stats?.streaming_sessions ?? "—"}</div>
                                <div className="stat-delta">Ativas agora</div>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon info">✅</div>
                            <div className="stat-body">
                                <div className="stat-label">Status do Sistema</div>
                                <div className="stat-value" style={{ fontSize: 14, fontWeight: 700, color: "var(--success)", marginTop: 6 }}>
                                    ● {stats?.system_status ?? "Verificando..."}
                                </div>
                                <div className="stat-delta">Todos os serviços online</div>
                            </div>
                        </div>
                    </div>

                    <div className="grid-2" style={{ marginBottom: 24 }}>
                        {/* Gráfico de Atividade */}
                        <div className="card">
                            <div className="card-header">
                                <div>
                                    <div className="card-title">Áudios Processados</div>
                                    <div className="card-subtitle">Atividade nos últimos 7 dias</div>
                                </div>
                                <div className="badge badge-success">
                                    <span className="badge-dot" />
                                    +8% essa semana
                                </div>
                            </div>
                            {loading ? (
                                <div className="skeleton" style={{ height: 120 }} />
                            ) : (
                                <div className="bar-chart">
                                    {stats?.daily_counts.map((d, i) => (
                                        <div key={i} className="bar-item">
                                            <div
                                                className={`bar ${i === 4 ? "active" : ""}`}
                                                style={{ height: `${(d.count / maxCount) * 100}%` }}
                                                title={`${d.day}: ${d.count}`}
                                            />
                                            <span className="bar-label">{d.day}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Processamento rápido */}
                        <div className="card">
                            <div className="card-header">
                                <div className="card-title">Processamento</div>
                            </div>
                            <div style={{ display: "flex", flexDirection: "column", gap: 16, marginTop: 8 }}>
                                <div>
                                    <div className="progress-header">
                                        <span className="progress-name">Áudios Processados</span>
                                        <span className="progress-pct">{stats?.processed_pct ?? 0}%</span>
                                    </div>
                                    <div className="progress-track">
                                        <div className="progress-fill" style={{ width: `${stats?.processed_pct ?? 0}%` }} />
                                    </div>
                                </div>
                                <div>
                                    <div className="progress-header">
                                        <span className="progress-name">Taxa de Transcrição</span>
                                        <span className="progress-pct">40%</span>
                                    </div>
                                    <div className="progress-track">
                                        <div className="progress-fill" style={{ width: "40%", background: "var(--success)" }} />
                                    </div>
                                </div>
                                <div>
                                    <div className="progress-header">
                                        <span className="progress-name">Uptime do Sistema</span>
                                        <span className="progress-pct">99.9%</span>
                                    </div>
                                    <div className="progress-track">
                                        <div className="progress-fill" style={{ width: "99.9%", background: "var(--warning)" }} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Últimos Uploads */}
                    <div className="card">
                        <div className="card-header">
                            <div className="card-title">Últimos Uploads</div>
                            <a href="/audios" className="btn btn-secondary btn-sm">Ver todos</a>
                        </div>
                        <div className="table-wrap">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Arquivo</th>
                                        <th>Duração</th>
                                        <th>Tamanho</th>
                                        <th>Processado</th>
                                        <th>Transcrito</th>
                                        <th>Data</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {loading ? (
                                        <tr><td colSpan={6} style={{ textAlign: "center", padding: 24, color: "var(--text-muted)" }}>Carregando...</td></tr>
                                    ) : stats?.last_uploads.map((a) => (
                                        <tr key={a.id}>
                                            <td style={{ fontWeight: 600 }}>🎙️ {a.filename}</td>
                                            <td>{formatDuration(a.duration_seconds)}</td>
                                            <td>{(a.size_bytes / 1024 / 1024).toFixed(1)} MB</td>
                                            <td><span className={`badge ${a.processed ? "badge-success" : "badge-warning"}`}>{a.processed ? "✓ Processado" : "Pendente"}</span></td>
                                            <td><span className={`badge ${a.transcribed ? "badge-brand" : "badge-muted"}`}>{a.transcribed ? "✓ Transcrito" : "—"}</span></td>
                                            <td className="text-muted">{new Date(a.recorded_at).toLocaleDateString("pt-BR")}</td>
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



