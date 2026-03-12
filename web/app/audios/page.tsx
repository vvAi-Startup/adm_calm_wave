"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { audiosAPI, Audio } from "../lib/api";

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

    // Batch Selection Data
    const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
    const [exporting, setExporting] = useState(false);

    const fetchAudios = () => {
        setLoading(true);
        const params: Record<string, string> = { page: currentPage.toString() };
        if (filter === "processed") params.processed = "true";
        if (filter === "pending") params.processed = "false";

        audiosAPI
            .list(params)
            .then((res) => { setAudios(res.audios); setTotal(res.total); setPages(res.pages); })
            .catch(() => { setAudios([]); setTotal(0); setPages(1); })
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
            setSelectedIds(prev => {
                const updated = new Set(prev);
                updated.delete(id);
                return updated;
            });
        } catch {
            alert("Erro ao remover.");
        } finally {
            setActionLoading(null);
        }
    };

    const toggleSelection = (id: number) => {
        setSelectedIds(prev => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });
    };

    const toggleAll = () => {
        if (selectedIds.size === filtered.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(filtered.map(a => a.id)));
        }
    };

    const handleBatchExport = async () => {
        if (selectedIds.size === 0) return;
        setExporting(true);
        try {
            const token = localStorage.getItem("calmwave_token");
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"}/api/audios/batch-export`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ audio_ids: Array.from(selectedIds) })
            });

            if (!res.ok) throw new Error("Falha ao exportar lote");

            // Baixar o ZIP retornado (blob)
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `calmwave_export_${new Date().getTime()}.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            setSelectedIds(new Set());
        } catch (error) {
            console.error(error);
            alert("Erro ao exportar áudios compactados.");
        } finally {
            setExporting(false);
        }
    };

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main">
                <Header title="Gerenciamento de Áudios" subtitle="Gerencie, filtre e visualize os arquivos processados pela IA" />
                <div className="page-content">
                    <div className="stats-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
                        <div className="stat-card"><div className="stat-icon brand">🎙️</div><div className="stat-body"><div className="stat-label">Total</div><div className="stat-value">{total}</div></div></div>
                        <div className="stat-card"><div className="stat-icon success">✅</div><div className="stat-body"><div className="stat-label">Processados</div><div className="stat-value">{audios.filter(a => a.processed).length}</div></div></div>
                        <div className="stat-card"><div className="stat-icon brand">📝</div><div className="stat-body"><div className="stat-label">Transcritos</div><div className="stat-value">{audios.filter(a => a.transcribed).length}</div></div></div>
                        <div className="stat-card"><div className="stat-icon warning">⭐</div><div className="stat-body"><div className="stat-label">Favoritos</div><div className="stat-value">{audios.filter(a => a.favorite).length}</div></div></div>
                    </div>

                    <div className="card">
                        <div className="card-header">
                            <div className="card-title">Lista de Áudios</div>
                            <div className="filters-bar" style={{ margin: 0 }}>
                                {selectedIds.size > 0 && (
                                    <button
                                        className="btn btn-secondary"
                                        onClick={handleBatchExport}
                                        disabled={exporting}
                                        style={{ marginRight: 8, borderColor: 'var(--brand)', color: 'var(--brand)' }}
                                    >
                                        {exporting ? "⏳ Gerando ZIP..." : `📦 Baixar ${selectedIds.size} selecionados (ZIP)`}
                                    </button>
                                )}
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
                                    <input placeholder="Buscar arquivo..." value={search} onChange={(e) => setSearch(e.target.value)} disabled={loading} />
                                </div>
                                <select className="select" style={{ width: "auto" }} value={filter} onChange={(e) => setFilter(e.target.value)} disabled={loading}>
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
                                        <th style={{ width: 40, textAlign: "center" }}>
                                            <input
                                                type="checkbox"
                                                checked={filtered.length > 0 && selectedIds.size === filtered.length}
                                                onChange={toggleAll}
                                            />
                                        </th>
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
                                        <tr><td colSpan={9} style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>Carregando dados da API...</td></tr>
                                    ) : filtered.length === 0 ? (
                                        <tr><td colSpan={9}><div className="empty-state"><div className="empty-icon">🎙️</div><div className="empty-title">Nenhum áudio encontrado</div></div></td></tr>
                                    ) : filtered.map((audio) => (
                                        <tr key={audio.id} style={{ background: selectedIds.has(audio.id) ? 'var(--bg-muted)' : 'transparent' }}>
                                            <td style={{ textAlign: "center" }}>
                                                <input
                                                    type="checkbox"
                                                    checked={selectedIds.has(audio.id)}
                                                    onChange={() => toggleSelection(audio.id)}
                                                />
                                            </td>
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
