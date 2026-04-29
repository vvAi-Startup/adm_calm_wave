"use client";
import { useState } from "react";
import Sidebar from "../../components/Sidebar";
import Header from "../../components/Header";
import { adminNotificationsAPI } from "../../lib/api";
import { toast } from "react-hot-toast";

export default function NotificationsPage() {
    const [title, setTitle] = useState("");
    const [message, setMessage] = useState("");
    const [type, setType] = useState("info");
    const [loading, setLoading] = useState(false);

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!title.trim() || !message.trim()) {
            toast.error("Preencha todos os campos obrigatórios.");
            return;
        }

        setLoading(true);
        const loadingToast = toast.loading("Disparando notificação...");

        try {
            await adminNotificationsAPI.broadcast({ title, message, type });
            
            toast.success("Notificação enviada a todos da rede CalmWave!", {
                id: loadingToast,
            });
            
            setTitle("");
            setMessage("");
            setType("info");
        } catch (e: unknown) {
            toast.error(e.message || "Erro de conexão ao enviar notificação.", {
                id: loadingToast,
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main">
                <Header title="Notificar Todos" subtitle="Dispare avisos pop-ups internos globais" />
                
                <div className="page-content">
                    <div style={{ maxWidth: "600px", margin: "0 auto", width: "100%" }}>
                        <div className="card">
                            <div className="card-header" style={{ borderBottom: "1px solid var(--border)", paddingBottom: "16px", marginBottom: "16px" }}>
                                <div className="card-title" style={{ fontSize: "18px", fontWeight: "600", display: "flex", alignItems: "center", gap: "8px" }}>
                                    <span>📢</span> Nova Transmissão (Broadcast)
                                </div>
                                <p style={{ fontSize: "14px", color: "var(--text-muted)", marginTop: "4px" }}>
                                    Esta notificação será enviada para o painel de todos os usuários registrados.
                                </p>
                            </div>
                            
                            <div style={{ padding: "0 8px 8px 8px" }}>
                                <form onSubmit={handleSend} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                                    
                                    <div className="form-group" style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                                        <label style={{ fontWeight: "500", fontSize: "14px", color: "var(--text-main)" }}>
                                            Título da Notificação <span style={{ color: "var(--danger)" }}>*</span>
                                        </label>
                                        <input
                                            type="text"
                                            className="form-control"
                                            required
                                            value={title}
                                            onChange={e => setTitle(e.target.value)}
                                            placeholder="Ex: Atualização Importante do Sistema"
                                            style={{
                                                padding: "10px 14px",
                                                borderRadius: "8px",
                                                border: "1px solid var(--border)",
                                                background: "var(--bg-box)",
                                                fontSize: "14px",
                                                color: "var(--text-main)",
                                                width: "100%",
                                                boxSizing: "border-box"
                                            }}
                                        />
                                    </div>

                                    <div className="form-group" style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                                        <label style={{ fontWeight: "500", fontSize: "14px", color: "var(--text-main)" }}>
                                            Mensagem <span style={{ color: "var(--danger)" }}>*</span>
                                        </label>
                                        <textarea
                                            className="form-control"
                                            required
                                            rows={4}
                                            value={message}
                                            onChange={e => setMessage(e.target.value)}
                                            placeholder="Descreva o comunicado ou instrução de forma clara..."
                                            style={{
                                                padding: "10px 14px",
                                                borderRadius: "8px",
                                                border: "1px solid var(--border)",
                                                background: "var(--bg-box)",
                                                fontSize: "14px",
                                                color: "var(--text-main)",
                                                resize: "vertical",
                                                minHeight: "100px",
                                                width: "100%",
                                                boxSizing: "border-box"
                                            }}
                                        />
                                    </div>

                                    <div className="form-group" style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                                        <label style={{ fontWeight: "500", fontSize: "14px", color: "var(--text-main)" }}>
                                            Tipo (Severidade Visual)
                                        </label>
                                        <select 
                                            className="form-control" 
                                            value={type} 
                                            onChange={e => setType(e.target.value)}
                                            style={{
                                                padding: "10px 14px",
                                                borderRadius: "8px",
                                                border: "1px solid var(--border)",
                                                background: "var(--bg-box)",
                                                fontSize: "14px",
                                                color: "var(--text-main)",
                                                width: "100%",
                                                cursor: "pointer"
                                            }}
                                        >
                                            <option value="info">ℹ️ Informativo Normal</option>
                                            <option value="success">✅ Sucesso / Conquista</option>
                                            <option value="warning">⚠️ Alerta Importante</option>
                                            <option value="danger">🚨 Ação Perigosa / Urgente</option>
                                        </select>
                                    </div>

                                    <button 
                                        type="submit" 
                                        className="btn btn-primary" 
                                        disabled={loading} 
                                        style={{ 
                                            marginTop: "10px",
                                            padding: "12px", 
                                            justifyContent: "center",
                                            fontSize: "15px",
                                            fontWeight: "600",
                                            display: "flex",
                                            alignItems: "center",
                                            gap: "8px",
                                            opacity: loading ? 0.7 : 1,
                                            cursor: loading ? "not-allowed" : "pointer"
                                        }}
                                    >
                                        {loading ? (
                                            <>
                                                <span className="spinner" style={{ width: "18px", height: "18px", border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "white", borderRadius: "50%", animation: "spin 1s linear infinite" }}></span>
                                                Disparando Notificações...
                                            </>
                                        ) : (
                                            <>
                                                <span>📢</span> Enviar para Toda a Rede
                                            </>
                                        )}
                                    </button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
