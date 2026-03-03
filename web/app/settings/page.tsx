"use client";
import { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { useAuth } from "../context/AuthContext";
import { usersAPI } from "../lib/api";

export default function SettingsPage() {
    const { user, login } = useAuth(); // Assuming login or updateUser context to update local state

    // Fallback logic for name
    const [name, setName] = useState(user?.name || "");
    const [darkMode, setDarkMode] = useState(user?.settings?.dark_mode ?? false);
    const [notifications, setNotifications] = useState(user?.settings?.notifications_enabled ?? true);
    const [autoProcess, setAutoProcess] = useState(user?.settings?.auto_process_audio ?? true);
    const [audioQuality, setAudioQuality] = useState(user?.settings?.audio_quality || "high");
    const [transcriptionLanguage, setTranscriptionLanguage] = useState(user?.transcription_language || "pt-BR");
    const [saved, setSaved] = useState(false);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (user) {
            setName(user.name);
            setTranscriptionLanguage(user.transcription_language || "pt-BR");
            if (user.settings) {
                setDarkMode(user.settings.dark_mode);
                setNotifications(user.settings.notifications_enabled);
                setAutoProcess(user.settings.auto_process_audio);
                setAudioQuality(user.settings.audio_quality);
            }
        }
    }, [user]);

    const handleSave = async () => {
        setLoading(true);
        try {
            const res = await usersAPI.updateSettings({
                name,
                transcription_language: transcriptionLanguage,
                dark_mode: darkMode,
                notifications_enabled: notifications,
                auto_process_audio: autoProcess,
                audio_quality: audioQuality
            });
            setSaved(true);
            setTimeout(() => setSaved(false), 2500);

            // Optionally update context user here if AuthContext allows
            // if (login) login(res.token, res.user) -- or whatever method AuthContext provides
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main">
                <Header title="Configurações de Perfil" subtitle="Gerencie suas preferências e configurações da conta" />
                <div className="page-content">
                    <div className="grid-2" style={{ alignItems: "start" }}>
                        {/* Perfil */}
                        <div className="card">
                            <div className="card-header"><div className="card-title">👤 Informações do Perfil</div></div>
                            <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 24 }}>
                                <div className="sidebar-avatar" style={{ width: 64, height: 64, fontSize: 28, borderRadius: 16 }}>
                                    {name.charAt(0).toUpperCase()}
                                </div>
                                <div>
                                    <div style={{ fontWeight: 700, fontSize: 16 }}>{name}</div>
                                    <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>{user?.email || "admin@calmwave.com"}</div>
                                    <div style={{ marginTop: 8 }}><span className="badge badge-brand">{user?.account_type || "admin"}</span></div>
                                </div>
                            </div>
                            <div className="form-group">
                                <label className="form-label">Nome</label>
                                <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Email</label>
                                <input className="input" value={user?.email || "admin@calmwave.com"} disabled style={{ opacity: 0.6 }} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Nova Senha</label>
                                <input className="input" type="password" placeholder="••••••••" />
                            </div>
                        </div>

                        {/* Preferências */}
                        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                            <div className="card">
                                <div className="card-header"><div className="card-title">⚙️ Preferências</div></div>
                                {[
                                    { label: "Tema Escuro", value: darkMode, onChange: setDarkMode, desc: "Ativar tema escuro no painel" },
                                    { label: "Notificações Ativas", value: notifications, onChange: setNotifications, desc: "Receber alertas de sistema" },
                                    { label: "Limpeza Automática", value: autoProcess, onChange: setAutoProcess, desc: "Processar áudios automaticamente" },
                                ].map((pref, i) => (
                                    <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 0", borderBottom: i < 2 ? "1px solid var(--border)" : "none" }}>
                                        <div>
                                            <div style={{ fontWeight: 600, fontSize: 14 }}>{pref.label}</div>
                                            <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{pref.desc}</div>
                                        </div>
                                        <button
                                            onClick={() => pref.onChange(!pref.value)}
                                            style={{
                                                width: 44, height: 24, borderRadius: 12, border: "none", cursor: "pointer",
                                                background: pref.value ? "var(--brand)" : "var(--border)",
                                                transition: "background 0.2s", position: "relative",
                                            }}
                                        >
                                            <div style={{
                                                width: 18, height: 18, background: "white", borderRadius: "50%", position: "absolute",
                                                top: 3, left: pref.value ? 23 : 3, transition: "left 0.2s",
                                            }} />
                                        </button>
                                    </div>
                                ))}

                                <div style={{ marginTop: 16 }}>
                                    <label className="form-label">Qualidade de Áudio</label>
                                    <select className="select" value={audioQuality} onChange={(e) => setAudioQuality(e.target.value)}>
                                        <option value="high">Alta (WAV 44.1kHz)</option>
                                        <option value="medium">Média (MP3 192kbps)</option>
                                        <option value="low">Baixa (MP3 128kbps)</option>
                                    </select>
                                </div>

                                <div style={{ marginTop: 16 }}>
                                    <label className="form-label">Idioma de Transcrição Padrão</label>
                                    <select className="select" value={transcriptionLanguage} onChange={(e) => setTranscriptionLanguage(e.target.value)}>
                                        <option value="pt-BR">Português (Brasil)</option>
                                        <option value="en-US">Inglês (Estados Unidos)</option>
                                        <option value="es-ES">Espanhol (Espanha)</option>
                                        <option value="auto">Detectar Automagicamente</option>
                                    </select>
                                    <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                                        O modelo Whisper usará este idioma para otimizar precisão e timestamps.
                                    </div>
                                </div>
                            </div>

                            <div style={{ display: "flex", gap: 12 }}>
                                <button className="btn btn-primary w-full" onClick={handleSave} disabled={loading}>
                                    {loading ? "⏳ Salvando..." : saved ? "✓ Salvo!" : "💾 Salvar Alterações"}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
