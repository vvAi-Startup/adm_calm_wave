"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { audiosAPI, Audio } from "../lib/api";

const MOCK_AUDIOS: Audio[] = [
    { id: 1, user_id: 1, filename: "reuniao_produto_2026.wav", duration_seconds: 1847, size_bytes: 17825792, recorded_at: "2026-02-24T14:30:00Z", processed: true, transcribed: true, favorite: true, device_origin: "Samsung S23" },
    { id: 2, user_id: 2, filename: "entrevista_cliente.wav", duration_seconds: 923, size_bytes: 8912896, recorded_at: "2026-02-24T11:15:00Z", processed: true, transcribed: false, favorite: false, device_origin: "iPhone 15" },
    { id: 3, user_id: 3, filename: "notas_pessoais_24fev.wav", duration_seconds: 312, size_bytes: 3014656, recorded_at: "2026-02-24T09:00:00Z", processed: false, transcribed: false, favorite: false, device_origin: "Motorola Moto G" },
    { id: 4, user_id: 1, filename: "podcast_ep12.wav", duration_seconds: 3612, size_bytes: 34836480, recorded_at: "2026-02-23T16:45:00Z", processed: true, transcribed: true, favorite: true, device_origin: "Samsung S23" },
    { id: 5, user_id: 4, filename: "aula_ingles.wav", duration_seconds: 5400, size_bytes: 52224000, recorded_at: "2026-02-23T10:00:00Z", processed: true, transcribed: false, favorite: false, device_origin: "Xiaomi Redmi" },
];

function formatDuration(s: number) {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m ${sec}s`;
}

export default function AudiosPage() {
    const router = useRouter();
    const [audios, setAudios] = useState<Audio[]>([]);
    const [total, setTotal] = useState(0);
    const [pages, setPages] = useState(1);
    const [currentPage, setCurrentPage] = useState(1);
    const [search, setSearch] = useState("");
    const [filter, setFilter] = useState("all");
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<number | null>(null);
    const [playerAudio, setPlayerAudio] = useState<Audio | null>(null);
    const [uploading, setUploading] = useState(false);

    const fetchAudios = () => {
        setLoading(true);
        const params: Record<string, string> = { page: currentPage.toString() };
        if (filter === "processed") params.processed = "true";
        if (filter === "pending") params.processed = "false";

        audiosAPI
            .list(params)
            .then((res) => { setAudios(res.audios); setTotal(res.total); setPages(res.pages); })
            .catch(() => { setAudios(MOCK_AUDIOS); setTotal(MOCK_AUDIOS.length); setPages(1); })
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        fetchAudios();
    }, [filter, currentPage]);

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploading(true);
        try {
            await audiosAPI.upload(file);
            alert("Áudio enviado e processado com sucesso!");
            fetchAudios(); // Recarrega a lista
        } catch (error) {
            alert("Erro ao enviar áudio.");
            console.error(error);
        } finally {
            setUploading(false);
            // Limpa o input
            e.target.value = '';
        }
    };

    const filtered = audios.filter((a) =>
        a.filename.toLowerCase().includes(search.toLowerCase())
    );

    const handleDelete = async (id: number) => {
        if (!confirm("Remover este áudio?")) return;
        setActionLoading(id);
        try {
            await audiosAPI.delete(id);
            setAudios((prev) => prev.filter((a) => a.id !== id));
        } catch { 
            alert("Erro ao remover."); 
            // Fallback for mock data
            setAudios((prev) => prev.filter((a) => a.id !== id));
        } finally {
            setActionLoading(null);
        }
    };

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main">
                <Header title="Gerenciamento de Áudios" subtitle="Gerencie, filtre e visualize os arquivos processados pela IA" />
                <div className="page-content">
                    <div className="stats-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
                        <div className="stat-card"><div className="stat-icon brand">🎙️</div><div className="stat-body"><div className="stat-label">Total</div><div className="stat-value">{total || MOCK_AUDIOS.length}</div></div></div>
                        <div className="stat-card"><div className="stat-icon success">✅</div><div className="stat-body"><div className="stat-label">Processados</div><div className="stat-value">{audios.filter(a => a.processed).length || 4}</div></div></div>
                        <div className="stat-card"><div className="stat-icon brand">📝</div><div className="stat-body"><div className="stat-label">Transcritos</div><div className="stat-value">{audios.filter(a => a.transcribed).length || 2}</div></div></div>
                        <div className="stat-card"><div className="stat-icon warning">⭐</div><div className="stat-body"><div className="stat-label">Favoritos</div><div className="stat-value">{audios.filter(a => a.favorite).length || 2}</div></div></div>
                    </div>

                    <div className="card">
                        <div className="card-header">
                            <div className="card-title">Lista de Áudios</div>
                            <div className="filters-bar" style={{ margin: 0 }}>
                                <div style={{ position: 'relative' }}>
                                    <input 
                                        type="file" 
                                        accept="audio/*" 
                                        onChange={handleUpload} 
                                        style={{ display: 'none' }} 
                                        id="audio-upload" 
                                        disabled={uploading}
                                    />
                                    <label 
                                        htmlFor="audio-upload" 
                                        className="btn btn-primary" 
                                        style={{ cursor: uploading ? 'not-allowed' : 'pointer', opacity: uploading ? 0.7 : 1 }}
                                    >
                                        {uploading ? "⏳ Processando..." : "⬆️ Fazer Upload"}
                                    </label>
                                </div>
                                <div className="search-bar" style={{ width: 240 }}>
                                    <span>🔍</span>
                                    <input placeholder="Buscar arquivo..." value={search} onChange={(e) => setSearch(e.target.value)} />
                                </div>
                                <select className="select" style={{ width: "auto" }} value={filter} onChange={(e) => setFilter(e.target.value)}>
                                    <option value="all">Todos</option>
                                    <option value="processed">Processados</option>
                                    <option value="pending">Pendentes</option>
                                </select>
                            </div>
                        </div>

                        <div className="table-wrap">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Arquivo</th>
                                        <th>Dispositivo</th>
                                        <th>Duração</th>
                                        <th>Tamanho</th>
                                        <th>Status</th>
                                        <th>Transcrição</th>
                                        <th>Data</th>
                                        <th>Ações</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {loading ? (
                                        <tr><td colSpan={8} style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>Carregando...</td></tr>
                                    ) : filtered.length === 0 ? (
                                        <tr><td colSpan={8}><div className="empty-state"><div className="empty-icon">🎙️</div><div className="empty-title">Nenhum áudio encontrado</div></div></td></tr>
                                    ) : filtered.map((audio) => (
                                        <tr key={audio.id}>
                                            <td>
                                                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                                    {audio.favorite && <span title="Favorito">⭐</span>}
                                                    <span style={{ fontWeight: 600, maxWidth: 220, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", display: "block" }}>{audio.filename}</span>
                                                </div>
                                            </td>
                                            <td className="text-muted">{audio.device_origin || "—"}</td>
                                            <td>{formatDuration(audio.duration_seconds)}</td>
                                            <td>{audio.size_bytes < 1024 * 1024 ? `${(audio.size_bytes / 1024).toFixed(1)} KB` : `${(audio.size_bytes / 1024 / 1024).toFixed(1)} MB`}</td>
                                            <td><span className={`badge ${audio.processed ? "badge-success" : "badge-warning"}`}><span className="badge-dot" />{audio.processed ? "Processado" : "Pendente"}</span></td>
                                            <td><span className={`badge ${audio.transcribed ? "badge-brand" : "badge-muted"}`}>{audio.transcribed ? "✓ Transcrito" : "—"}</span></td>
                                            <td className="text-muted">{new Date(audio.recorded_at).toLocaleDateString("pt-BR")}</td>
                                            <td>
                                                <div style={{ display: "flex", gap: 6 }}>
                                                    <button className="btn-icon" title="Ver Detalhes" onClick={() => router.push(`/audios/${audio.id}`)}>👁️</button>
                                                    <button className="btn-icon" title="Ouvir" onClick={() => setPlayerAudio(audio)}>▶</button>
                                                    <button 
                                                        className="btn-icon" 
                                                        onClick={() => handleDelete(audio.id)} 
                                                        title="Remover" 
                                                        style={{ color: "var(--danger)", opacity: actionLoading === audio.id ? 0.5 : 1 }}
                                                        disabled={actionLoading === audio.id}
                                                    >
                                                        {actionLoading === audio.id ? "⏳" : "🗑"}
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        
                        {/* Pagination Controls */}
                        {pages > 1 && (
                            <div style={{ display: "flex", justifyContent: "center", gap: 8, padding: 16, borderTop: "1px solid var(--border)" }}>
                                <button 
                                    className="btn btn-secondary btn-sm" 
                                    disabled={currentPage === 1}
                                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                >
                                    Anterior
                                </button>
                                <span style={{ display: "flex", alignItems: "center", fontSize: 14 }}>
                                    Página {currentPage} de {pages}
                                </span>
                                <button 
                                    className="btn btn-secondary btn-sm" 
                                    disabled={currentPage === pages}
                                    onClick={() => setCurrentPage(p => Math.min(pages, p + 1))}
                                >
                                    Próxima
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </main>

            {/* Player Modal */}
            {playerAudio && (
                <div className="modal-overlay" onClick={() => setPlayerAudio(null)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-title">🎙️ Player de Áudio</div>
                        <div className="modal-subtitle">{playerAudio.filename}</div>
                        <div className="player" style={{ marginTop: 16 }}>
                            <audio 
                                controls 
                                autoPlay 
                                style={{ width: '100%' }}
                                src={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"}/api/audios/play/${playerAudio.id}`}
                            >
                                Seu navegador não suporta o elemento de áudio.
                            </audio>
                        </div>
                        <div style={{ marginTop: 16, display: "flex", gap: 8, justifyContent: "flex-end" }}>
                            <button className="btn btn-secondary" onClick={() => setPlayerAudio(null)}>Fechar</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
