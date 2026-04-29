"use client";
import { useState, useEffect } from "react";
import { io, Socket } from "socket.io-client";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";

interface Session {
    id: string;
    user: string;
    device: string;
    connected_at: string;
    duration: string;
    messages: number;
    status: string;
}

export default function StreamingPage() {
    const [sessions, setSessions] = useState<Session[]>([]);
    const [loading, setLoading] = useState(true);
    const [socket, setSocket] = useState<Socket | null>(null);
    const [stats, setStats] = useState({
        active_sessions: 0,
        messages_per_min: 0,
        latency_ms: 0,
        bandwidth_mbps: 0
    });

    useEffect(() => {
        const fetchSessions = async () => {
            try {
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"}/api/streaming/sessions`);
                const data = await res.json();
                if (data.sessions) {
                    setSessions(data.sessions);
                }
            } catch (error) {
                console.error("Failed to fetch initial sessions", error);
            }
        };
        fetchSessions();

        const newSocket = io(process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000", {
            path: "/socket.io",
            transports: ["websocket", "polling"]
        });

        /* eslint-disable react-hooks/set-state-in-effect */
        setSocket(newSocket);

        newSocket.on("connect", () => {
            console.log("Connected to WebSocket server");
        });

        newSocket.on("session_update", (data) => {
            if (data.action === 'add') {
                setSessions(prev => {
                    // Check if already exists to prevent duplicates
                    if (prev.some(s => s.id === data.session.id)) return prev;
                    return [...prev, {
                        id: data.session.id || data.id,
                        user: data.session.user,
                        device: data.session.device,
                        connected_at: data.session.connected_at,
                        duration: "0m 0s",
                        messages: 0,
                        status: "online"
                    }];
                });
            } else if (data.action === 'remove') {
                setSessions(prev => prev.filter(s => s.id !== data.id));
            } else if (data.sessions) {
                // Full list update
                setSessions(data.sessions);
            }
            setLoading(false);
        });

        newSocket.on("session_stats", (data) => {
            // Update specific session stats
            if (data.id) {
                setSessions(prev => prev.map(s => 
                    s.id === data.id ? { ...s, messages: data.messages } : s
                ));
            }
            
            // Update global stats if provided
            if (data.active_sessions !== undefined) {
                setStats(prev => ({...prev, ...data}));
            }
        });

        newSocket.on("disconnect", () => {
            console.log("Disconnected from WebSocket server");
        });

        return () => {
            newSocket.disconnect();
        };
    }, []);

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main">
                <Header title="Streaming WebSocket" subtitle="Sessões de gravação em tempo real" />
                <div className="page-content">
                    <div className="stats-grid" style={{ gridTemplateColumns: "repeat(4,1fr)" }}>
                        <div className="stat-card"><div className="stat-icon brand">📡</div><div className="stat-body"><div className="stat-label">Sessões Ativas</div><div className="stat-value">{stats.active_sessions || sessions.length}</div></div></div>
                        <div className="stat-card"><div className="stat-icon success">💬</div><div className="stat-body"><div className="stat-label">Mensagens/min</div><div className="stat-value">{stats.messages_per_min || 0}</div></div></div>
                        <div className="stat-card"><div className="stat-icon warning">⚡</div><div className="stat-body"><div className="stat-label">Latência WS</div><div className="stat-value">{stats.latency_ms || 0}ms</div></div></div>
                        <div className="stat-card"><div className="stat-icon info">📶</div><div className="stat-body"><div className="stat-label">Banda Total</div><div className="stat-value">{stats.bandwidth_mbps || 0} MB/s</div></div></div>
                    </div>

                    <div className="card">
                        <div className="card-header">
                            <div className="card-title">Sessões WebSocket Ativas</div>
                            <div className="badge badge-success"><span className="badge-dot" />Live</div>
                        </div>

                        {/* Live waveform demo */}
                        <div style={{ background: "var(--bg-muted)", borderRadius: "var(--radius)", padding: 20, marginBottom: 20 }}>
                            <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 12 }}>📡 Feed ao vivo — sesión ws_001</div>
                            <div className="waveform" style={{ height: 80 }}>
                                {Array.from({ length: 60 }).map((_, i) => (
                                    <div
                                        key={i}
                                        className="wave-bar played"
                                        style={{ height: `${15 + Math.abs(Math.sin(i * 0.4)) * 65 + (i % 10) * 2}%`, opacity: 0.6 + (i / 60) * 0.4 }}
                                    />
                                ))}
                            </div>
                        </div>

                        <div className="table-wrap">
                            <table>
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Usuário</th>
                                        <th>Dispositivo</th>
                                        <th>Conectado</th>
                                        <th>Duração</th>
                                        <th>Msgs</th>
                                        <th>Status</th>
                                        <th>Ações</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {sessions.length === 0 ? (
                                        <tr>
                                            <td colSpan={8} style={{ textAlign: "center", padding: "40px 0", color: "var(--text-muted)" }}>
                                                Nenhuma sessão de streaming ativa no momento.
                                            </td>
                                        </tr>
                                    ) : (
                                        sessions.map((s) => (
                                            <tr key={s.id}>
                                                <td><code style={{ fontSize: 12, background: "var(--bg-muted)", padding: "2px 6px", borderRadius: 4 }}>{s.id.substring(0, 8)}...</code></td>
                                                <td style={{ fontWeight: 600 }}>{s.user}</td>
                                                <td className="text-muted">{s.device}</td>
                                                <td className="text-muted">{new Date(s.connected_at).toLocaleTimeString("pt-BR")}</td>
                                                <td>{s.duration}</td>
                                                <td>{s.messages}</td>
                                                <td><span className="badge badge-success"><span className="badge-dot" />Online</span></td>
                                                <td><button className="btn-icon" title="Encerrar sessão" style={{ color: "var(--danger)" }}>✕</button></td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
