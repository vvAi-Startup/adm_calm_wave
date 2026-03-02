"use client";
import { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { usersAPI, Device } from "../lib/api";

export default function PrivacyPage() {
    const [devices, setDevices] = useState<Device[]>([]);
    const [loading, setLoading] = useState(true);
    const [consentData, setConsentData] = useState(true);
    const [consentMarketing, setConsentMarketing] = useState(false);
    const [revokeAllDone, setRevokeAllDone] = useState(false);

    useEffect(() => {
        usersAPI.getDevices()
            .then(res => setDevices(res.devices))
            .catch(err => console.error("Falha ao carregar dispositivos", err))
            .finally(() => setLoading(false));
    }, []);

    const revokeDevice = async (id: number) => {
        try {
            await usersAPI.revokeDevice(id);
            setDevices((prev) => prev.filter((d) => d.id === id ? d.is_current : true));
        } catch (error) {
            console.error("Falha ao revogar:", error);
        }
    };
    
    const handleRevokeAll = async () => {
        try {
            await usersAPI.revokeAllDevices();
            setDevices(prev => prev.filter(d => d.is_current));
            setRevokeAllDone(true);
            setTimeout(() => setRevokeAllDone(false), 3000);
        } catch (error) {
            console.error("Falha ao revogar todos:", error);
        }
    }

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main">
                <Header title="Privacidade e Dispositivos" subtitle="Gerencie seus dados, consentimentos e sessões ativas" />
                <div className="page-content">
                    <div className="grid-2" style={{ alignItems: "start" }}>
                        {/* Dispositivos */}
                        <div className="card">
                            <div className="card-header"><div className="card-title">📱 Dispositivos Conectados</div></div>
                            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                                {loading ? (
                                    <div style={{ padding: 20, textAlign: "center", color: "var(--text-muted)" }}>Carregando dispositivos...</div>
                                ) : devices.length === 0 ? (
                                    <div style={{ padding: 20, textAlign: "center", color: "var(--text-muted)" }}>Nenhum dispositivo encontrado.</div>
                                ) : devices.map((d) => (
                                    <div key={d.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 0", borderBottom: "1px solid var(--border)" }}>
                                        <div style={{ display: "flex", gap: 12 }}>
                                            <span style={{ fontSize: 24 }}>{d.device_type?.includes("Mobile") || d.device_type?.includes("Android") ? "📱" : "💻"}</span>
                                            <div>
                                                <div style={{ fontWeight: 600, fontSize: 14 }}>{d.device_name} {d.is_current && <span className="badge badge-success" style={{ fontSize: 10 }}>atual</span>}</div>
                                                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{d.device_type} · IP: {d.ip_address}</div>
                                                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Visto em: {d.last_active ? new Date(d.last_active).toLocaleString("pt-BR") : "Desconhecido"}</div>
                                            </div>
                                        </div>
                                        {!d.is_current && (
                                            <button className="btn btn-danger btn-sm" onClick={() => revokeDevice(d.id)}>Revogar</button>
                                        )}
                                    </div>
                                ))}
                            </div>
                            <button
                                className="btn btn-danger w-full"
                                style={{ marginTop: 16 }}
                                onClick={handleRevokeAll}
                                disabled={devices.length <= 1}
                            >
                                {revokeAllDone ? "✓ Sessões encerradas" : "🚫 Encerrar todas as outros sessões"}
                            </button>
                        </div>

                        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                            {/* Consentimentos LGPD */}
                            <div className="card">
                                <div className="card-header"><div className="card-title">🔒 Consentimentos (LGPD)</div></div>
                                {[
                                    { label: "Coleta de dados de uso", desc: "Estatísticas de uso do app", value: consentData, onChange: setConsentData },
                                    { label: "Marketing e comunicações", desc: "Emails e notificações promocionais", value: consentMarketing, onChange: setConsentMarketing },
                                ].map((c, i) => (
                                    <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 0", borderBottom: i === 0 ? "1px solid var(--border)" : "none" }}>
                                        <div>
                                            <div style={{ fontWeight: 600, fontSize: 14 }}>{c.label}</div>
                                            <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{c.desc}</div>
                                        </div>
                                        <button
                                            onClick={() => c.onChange(!c.value)}
                                            style={{ width: 44, height: 24, borderRadius: 12, border: "none", cursor: "pointer", background: c.value ? "var(--brand)" : "var(--border)", position: "relative", transition: "background 0.2s" }}
                                        >
                                            <div style={{ width: 18, height: 18, background: "white", borderRadius: "50%", position: "absolute", top: 3, left: c.value ? 23 : 3, transition: "left 0.2s" }} />
                                        </button>
                                    </div>
                                ))}
                            </div>

                            {/* Seus dados */}
                            <div className="card">
                                <div className="card-header"><div className="card-title">📦 Seus Dados</div></div>
                                <p style={{ fontSize: 14, color: "var(--text-secondary)", marginBottom: 16 }}>
                                    Em conformidade com a LGPD, você pode exportar ou deletar todos os seus dados a qualquer momento.
                                </p>
                                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                                    <button className="btn btn-secondary w-full">⬇️ Exportar meus dados (.json)</button>
                                    <button className="btn btn-danger w-full">🗑️ Deletar conta e todos os dados</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
