"use client";
import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { playlistsAPI, Playlist } from "../lib/api";
import ProtectedRoute from "../components/ProtectedRoute";

export default function PlaylistsPage() {
    const [playlists, setPlaylists] = useState<Playlist[]>([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<number | null>(null);

    // Modal state for create/edit
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [currentPlaylist, setCurrentPlaylist] = useState<Partial<Playlist> | null>(null);

    const fetchPlaylists = async () => {
        setLoading(true);
        try {
            const res = await playlistsAPI.list({ per_page: 50 });
            setPlaylists(res.playlists);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPlaylists();
    }, []);

    const handleDelete = async (id: number) => {
        if (!confirm("Tem certeza que deseja remover esta playlist? Os áudios não serão apagados do sistema.")) return;
        setActionLoading(id);
        try {
            await playlistsAPI.delete(id);
            setPlaylists(prev => prev.filter(p => p.id !== id));
        } catch (error) {
            alert("Erro ao remover playlist.");
        } finally {
            setActionLoading(null);
        }
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!currentPlaylist?.name) return;

        try {
            if (currentPlaylist.id) {
                // Update
                const res = await playlistsAPI.update(currentPlaylist.id, {
                    name: currentPlaylist.name,
                    color: currentPlaylist.color || "#6FAF9E"
                });
                setPlaylists(prev => prev.map(p => p.id === res.playlist.id ? res.playlist : p));
            } else {
                // Create
                const res = await playlistsAPI.create({
                    name: currentPlaylist.name,
                    color: currentPlaylist.color || "#6FAF9E"
                });
                setPlaylists(prev => [...prev, res.playlist]);
            }
            setIsModalOpen(false);
            setCurrentPlaylist(null);
        } catch (error) {
            alert("Erro ao salvar playlist.");
        }
    };

    const openCreateModal = () => {
        setCurrentPlaylist({ name: "", color: "#6FAF9E" });
        setIsModalOpen(true);
    };

    const openEditModal = (playlist: Playlist) => {
        setCurrentPlaylist(playlist);
        setIsModalOpen(true);
    };

    return (
        <ProtectedRoute>
            <div className="app-layout">
                <Sidebar />
                <main className="app-main">
                    <Header title="Playlists e Pastas" subtitle="Organize seus áudios processados" />
                    <div className="page-content">

                        <div className="card">
                            <div className="card-header">
                                <div className="card-title">Minhas Playlists</div>
                                <div className="filters-bar" style={{ margin: 0 }}>
                                    <button className="btn btn-primary" onClick={openCreateModal}>
                                        ➕ Nova Playlist
                                    </button>
                                </div>
                            </div>

                            <div className="playlists-grid" style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                                gap: '16px',
                                padding: '16px'
                            }}>
                                {loading ? (
                                    <div style={{ color: "var(--text-muted)" }}>Carregando pastas...</div>
                                ) : playlists.length === 0 ? (
                                    <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
                                        <div className="empty-icon">🗂️</div>
                                        <div className="empty-title">Nenhuma playlist criada</div>
                                    </div>
                                ) : playlists.map(playlist => (
                                    <div key={playlist.id} className="stat-card" style={{
                                        position: 'relative',
                                        borderLeft: `4px solid ${playlist.color || 'var(--brand)'}`,
                                        alignItems: 'flex-start'
                                    }}>
                                        <div className="stat-icon" style={{ backgroundColor: `${playlist.color}20` || 'var(--brand-light)', color: playlist.color || 'var(--brand)' }}>
                                            🗂️
                                        </div>
                                        <div className="stat-body" style={{ flex: 1 }}>
                                            <div className="stat-label" style={{ fontSize: '1.1rem', color: 'var(--text)', fontWeight: 600 }}>
                                                {playlist.name}
                                            </div>
                                            <div className="stat-value" style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                                                {playlist.total_audios || 0} áudios
                                            </div>
                                        </div>

                                        <div style={{ position: 'absolute', top: '16px', right: '16px', display: 'flex', gap: '8px' }}>
                                            <button
                                                className="btn-icon"
                                                onClick={() => openEditModal(playlist)}
                                                title="Editar"
                                            >
                                                ✏️
                                            </button>
                                            <button
                                                className="btn-icon"
                                                onClick={() => handleDelete(playlist.id)}
                                                disabled={actionLoading === playlist.id}
                                                style={{ color: "var(--danger)" }}
                                                title="Remover"
                                            >
                                                {actionLoading === playlist.id ? "⏳" : "🗑"}
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </main>

                {/* Modal for Create/Edit */}
                {isModalOpen && (
                    <div className="modal-overlay" onClick={() => setIsModalOpen(false)}>
                        <div className="modal" onClick={(e) => e.stopPropagation()}>
                            <div className="modal-title">
                                {currentPlaylist?.id ? "✏️ Editar Playlist" : "➕ Nova Playlist"}
                            </div>
                            <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '16px' }}>
                                <div className="form-group">
                                    <label className="form-label">Nome da Pasta</label>
                                    <input
                                        type="text"
                                        className="input"
                                        value={currentPlaylist?.name || ""}
                                        onChange={e => setCurrentPlaylist({ ...currentPlaylist, name: e.target.value })}
                                        placeholder="Ex: Reuniões Importantes"
                                        required
                                        autoFocus
                                    />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Cor de Destaque</label>
                                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                        <input
                                            type="color"
                                            value={currentPlaylist?.color || "#6FAF9E"}
                                            onChange={e => setCurrentPlaylist({ ...currentPlaylist, color: e.target.value })}
                                            style={{ width: '40px', height: '40px', padding: '0', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                                        />
                                        <span style={{ color: "var(--text-muted)", fontSize: '0.9rem' }}>
                                            Escolha uma cor para identificar esta pasta
                                        </span>
                                    </div>
                                </div>

                                <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end", marginTop: "8px" }}>
                                    <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>Cancelar</button>
                                    <button type="submit" className="btn btn-primary">{currentPlaylist?.id ? "Salvar" : "Criar"}</button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}
            </div>
        </ProtectedRoute>
    );
}
