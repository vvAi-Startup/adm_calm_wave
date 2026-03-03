"use client";
import { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { supportAPI, SupportTicket } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import toast from "react-hot-toast";

export default function SupportPage() {
    const { user } = useAuth();
    const [tickets, setTickets] = useState<SupportTicket[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);
    const [replyText, setReplyText] = useState("");
    const [replying, setReplying] = useState(false);

    // For user creation
    const [newSubject, setNewSubject] = useState("");
    const [newMessage, setNewMessage] = useState("");
    const [creating, setCreating] = useState(false);
    const [showCreate, setShowCreate] = useState(false);

    const fetchTickets = async () => {
        try {
            const res = await supportAPI.list();
            setTickets(res.tickets);
        } catch (error) {
            console.error("Falha ao carregar tickets", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTickets();
    }, []);

    const handleSelectTicket = async (id: number) => {
        try {
            const res = await supportAPI.get(id);
            setSelectedTicket(res.ticket);
        } catch (error) {
            toast.error("Erro ao abrir ticket.");
        }
    };

    const handleReply = async () => {
        if (!selectedTicket || !replyText.trim()) return;
        setReplying(true);
        try {
            await supportAPI.reply(selectedTicket.id, replyText);
            setReplyText("");
            // Refresh ticket
            handleSelectTicket(selectedTicket.id);
            fetchTickets();
        } catch (error) {
            toast.error("Falha ao enviar resposta.");
        } finally {
            setReplying(false);
        }
    };

    const handleCreate = async () => {
        if (!newSubject.trim() || !newMessage.trim()) return;
        setCreating(true);
        try {
            await supportAPI.create({ subject: newSubject, message: newMessage });
            setShowCreate(false);
            setNewSubject("");
            setNewMessage("");
            fetchTickets();
            toast.success("Chamado aberto!");
        } catch (error) {
            toast.error("Falha ao abrir chamado.");
        } finally {
            setCreating(false);
        }
    };

    const statusBadge = (status: string) => {
        switch (status) {
            case "open": return <span className="badge badge-brand">Aberto</span>;
            case "answered": return <span className="badge badge-success">Respondido</span>;
            default: return <span className="badge">Fechado</span>;
        }
    };

    if (loading) return <div className="app-layout"><Sidebar /><main className="app-main"><div style={{ padding: 40 }}>Carregando...</div></main></div>;

    const isAdmin = user?.account_type === "admin";

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main">
                <Header title="Suporte Remoto" subtitle="Centro de Ajuda / Helpdesk via App Móvel" />
                <div className="page-content">

                    <div style={{ display: 'flex', gap: 24, height: 'calc(100vh - 160px)' }}>

                        {/* Lista de Tickets (Inbox) */}
                        <div className="card" style={{ flex: '0 0 350px', display: 'flex', flexDirection: 'column' }}>
                            <div className="card-header" style={{ justifyContent: 'space-between' }}>
                                <div className="card-title">Caixa de Entrada</div>
                                {!isAdmin && (
                                    <button className="btn btn-primary" onClick={() => setShowCreate(true)} style={{ padding: '4px 12px' }}>+ Novo</button>
                                )}
                            </div>
                            <div style={{ overflowY: 'auto', flex: 1, padding: 10 }}>
                                {tickets.length === 0 ? (
                                    <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>Nenhum chamado.</div>
                                ) : (
                                    tickets.map(t => (
                                        <div
                                            key={t.id}
                                            onClick={() => handleSelectTicket(t.id)}
                                            style={{
                                                padding: 16,
                                                borderBottom: '1px solid var(--border)',
                                                cursor: 'pointer',
                                                background: selectedTicket?.id === t.id ? 'var(--bg-muted)' : 'transparent',
                                                borderLeft: selectedTicket?.id === t.id ? '3px solid var(--brand)' : '3px solid transparent'
                                            }}
                                        >
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                                                <div style={{ fontWeight: 600, fontSize: 14 }}>#{t.id} - {t.subject}</div>
                                                {statusBadge(t.status)}
                                            </div>
                                            {isAdmin && <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Para: {t.user_email}</div>}
                                            <div style={{ fontSize: 13, color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                {t.last_message || "..."}
                                            </div>
                                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8, textAlign: 'right' }}>
                                                Atualização: {new Date(t.updated_at).toLocaleDateString()}
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>

                        {/* Visão do Chat/Detalhes */}
                        <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                            {showCreate && !isAdmin ? (
                                <div style={{ padding: 24 }}>
                                    <h3>Abrir Novo Chamado</h3>
                                    <p style={{ color: 'var(--text-muted)', marginBottom: 20 }}>Precisa de ajuda com o aplicativo móvel? Envie uma mensagem e o suporte responderá em breve via notificação.</p>

                                    <div className="form-group">
                                        <label className="form-label">Assunto</label>
                                        <input className="input" value={newSubject} onChange={e => setNewSubject(e.target.value)} placeholder="Ex: Erro ao sincronizar offline" />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Mensagem</label>
                                        <textarea className="input" style={{ minHeight: 150 }} value={newMessage} onChange={e => setNewMessage(e.target.value)} placeholder="Detalhe o seu problema..."></textarea>
                                    </div>
                                    <div>
                                        <button className="btn btn-primary" onClick={handleCreate} disabled={creating}>
                                            {creating ? "Enviando..." : "Enviar Solicitação"}
                                        </button>
                                        <button className="btn btn-secondary" onClick={() => setShowCreate(false)} style={{ marginLeft: 12 }}>Cancelar</button>
                                    </div>
                                </div>
                            ) : selectedTicket ? (
                                <>
                                    <div className="card-header" style={{ background: 'var(--bg-muted)', borderBottom: '1px solid var(--border)' }}>
                                        <div>
                                            <div className="card-title">#{selectedTicket.id} - {selectedTicket.subject}</div>
                                            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
                                                Solicitante: {selectedTicket.user_email} | Abertura: {new Date(selectedTicket.created_at).toLocaleString()}
                                            </div>
                                        </div>
                                        <div>{statusBadge(selectedTicket.status)}</div>
                                    </div>

                                    <div style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 16 }}>
                                        {selectedTicket.messages_list?.map(m => {
                                            const isMe = m.sender === (isAdmin ? 'admin' : 'user');
                                            return (
                                                <div key={m.id} style={{
                                                    alignSelf: isMe ? 'flex-end' : 'flex-start',
                                                    maxWidth: '70%'
                                                }}>
                                                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, textAlign: isMe ? 'right' : 'left' }}>
                                                        {m.sender.toUpperCase()} - {new Date(m.sent_at).toLocaleTimeString()}
                                                    </div>
                                                    <div style={{
                                                        background: isMe ? 'var(--brand)' : 'var(--bg-muted)',
                                                        color: isMe ? 'white' : 'var(--text-main)',
                                                        padding: 12,
                                                        borderRadius: 8,
                                                        borderBottomRightRadius: isMe ? 0 : 8,
                                                        borderBottomLeftRadius: isMe ? 8 : 0,
                                                        border: isMe ? 'none' : '1px solid var(--border)'
                                                    }}>
                                                        {m.message}
                                                    </div>
                                                </div>
                                            )
                                        })}
                                    </div>

                                    <div style={{ padding: 16, borderTop: '1px solid var(--border)', display: 'flex', gap: 12 }}>
                                        <input
                                            className="input"
                                            style={{ flex: 1 }}
                                            placeholder="Digite sua resposta..."
                                            value={replyText}
                                            onChange={e => setReplyText(e.target.value)}
                                            onKeyDown={e => { if (e.key === 'Enter') handleReply(); }}
                                        />
                                        <button className="btn btn-primary" onClick={handleReply} disabled={replying || !replyText.trim()}>
                                            {replying ? "..." : "Enviar"}
                                        </button>
                                    </div>
                                </>
                            ) : (
                                <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                                    <div style={{ textAlign: 'center' }}>
                                        <div style={{ fontSize: 40, marginBottom: 16 }}>💬</div>
                                        <div>Selecione um chamado na lista ao lado para começar.</div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
