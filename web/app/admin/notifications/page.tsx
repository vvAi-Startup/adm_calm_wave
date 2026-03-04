"use client";
import { useState } from "react";
import Sidebar from "../../components/Sidebar";
import Header from "../../components/Header";

export default function NotificationsPage() {
    const [title, setTitle] = useState("");
    const [message, setMessage] = useState("");
    const [type, setType] = useState("info");
    const [loading, setLoading] = useState(false);

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const token = localStorage.getItem("token");
            const response = await fetch("http://localhost:5000/api/admin/notifications/broadcast", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ title, message, type })
            });
            const data = await response.json();
            if (response.ok) {
                alert("Notificação enviada a todos da rede CalmWave.");
                setTitle("");
                setMessage("");
            } else {
                alert(data.error || "Erro ao enviar.");
            }
        } catch (e) {
            alert("Erro de conexão.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main">
                <Header title="Notificar Todos" subtitle="Dispare avisos pop-ups internos globais" />
                <div className="page-content" style={{ maxWidth: 600 }}>
                    <div className="card">
                        <div className="card-header">
                            <div className="card-title">Nova Transmissão (Broadcast)</div>
                        </div>
                        <div style={{ padding: 24 }}>
                            <form onSubmit={handleSend} style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                                <div className="form-group">
                                    <label>Título da Notificação</label>
                                    <input
                                        type="text"
                                        className="form-control"
                                        required
                                        value={title}
                                        onChange={e => setTitle(e.target.value)}
                                        placeholder="Atualização Importante"
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Mensagem</label>
                                    <textarea
                                        className="form-control"
                                        required
                                        rows={4}
                                        value={message}
                                        onChange={e => setMessage(e.target.value)}
                                        placeholder="Descreva o comunicado..."
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Tipo (Severidade UI)</label>
                                    <select className="form-control" value={type} onChange={e => setType(e.target.value)}>
                                        <option value="info">Informativo Normal</option>
                                        <option value="success">Sucesso / Conquista</option>
                                        <option value="warning">Alerta Importante</option>
                                        <option value="danger">Ação Perigosa / Urgente</option>
                                    </select>
                                </div>

                                <button type="submit" className="btn btn-primary" disabled={loading} style={{ justifyContent: "center" }}>
                                    {loading ? "Disparando..." : "📢 Enviar para Todos"}
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
