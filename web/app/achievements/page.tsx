"use client";
import { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { usersAPI, Achievement } from "../lib/api";

const defaultAchievements = [
    { id: 1, icon: "🏆", name: "Primeira Gravação", desc: "Gravou o primeiro áudio no app", earned: false, count: 0 },
    { id: 2, icon: "🎖️", name: "10 Gravações", desc: "Gravou 10 áudios", earned: false, count: 0 },
    { id: 3, icon: "🔥", name: "7 Dias Seguidos", desc: "Usou o app por 7 dias consecutivos", earned: false, count: 0 },
    { id: 4, icon: "🎵", name: "50 Áudios Limpos", desc: "Processou 50 áudios com IA", earned: false, count: 0 },
    { id: 5, icon: "⚡", name: "Gravação Longa (30min+)", desc: "Gravação com mais de 30 minutos", earned: false, count: 0 },
    { id: 6, icon: "📝", name: "Mestre da Transcrição", desc: "Transcreveu 20 áudios", earned: false, count: 0 },
    { id: 7, icon: "⭐", name: "Colecionador", desc: "Adicionou 10 favoritos", earned: false, count: 0 },
    { id: 8, icon: "🌙", name: "Coruja Noturna", desc: "Gravou após meia-noite 5x", earned: false, count: 0 },
];

export default function AchievementsPage() {
    const [achievements, setAchievements] = useState<Achievement[]>(defaultAchievements);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        usersAPI.getAchievements()
            .then(res => {
                // Merge real achievements with defaults
                const merged = defaultAchievements.map(defAff => {
                    const real = res.achievements.find(a => a.id === defAff.id);
                    return real ? { ...defAff, ...real } : defAff;
                });
                setAchievements(merged);
            })
            .catch(err => console.error(err))
            .finally(() => setLoading(false));
    }, []);

    const earned = achievements.filter(a => a.earned).length;
    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main">
                <Header title="Conquistas e Gamificação" subtitle="Acompanhe os marcos alcançados pelos usuários" />
                <div className="page-content">
                    <div className="stats-grid" style={{ gridTemplateColumns: "repeat(4,1fr)" }}>
                        <div className="stat-card"><div className="stat-icon brand">🏆</div><div className="stat-body"><div className="stat-label">Total de Conquistas</div><div className="stat-value">{achievements.length}</div></div></div>
                        <div className="stat-card"><div className="stat-icon success">✅</div><div className="stat-body"><div className="stat-label">Conquistadas</div><div className="stat-value">{earned}</div></div></div>
                        <div className="stat-card"><div className="stat-icon warning">🎖️</div><div className="stat-body"><div className="stat-label">Usuários com Conquistas</div><div className="stat-value">312</div></div></div>
                        <div className="stat-card"><div className="stat-icon info">📊</div><div className="stat-body"><div className="stat-label">Taxa de Engajamento</div><div className="stat-value">64%</div></div></div>
                    </div>

                    <div className="card">
                        <div className="card-header">
                            <div className="card-title">Todas as Conquistas</div>
                            <div style={{ display: "flex", gap: 8 }}>
                                <span className="badge badge-success">✅ Ativas: {earned}</span>
                                <span className="badge badge-muted">🔒 Bloqueadas: {achievements.length - earned}</span>
                            </div>
                        </div>
                        <div className="achievement-grid">
                            {achievements.map((a) => (
                                <div key={a.id} className={`achievement-card ${!a.earned ? "locked" : ""}`}>
                                    <div className="achievement-icon">{a.icon}</div>
                                    <div>
                                        <div className="achievement-name">{a.name}</div>
                                        <div className="achievement-desc">{a.desc}</div>
                                        <div style={{ marginTop: 8, fontSize: 12, color: "var(--text-muted)" }}>
                                            {a.count} usuários desbloquearam
                                        </div>
                                        {!a.earned && (
                                            <div style={{ marginTop: 6 }}>
                                                <span className="badge badge-muted">🔒 Bloqueado</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
