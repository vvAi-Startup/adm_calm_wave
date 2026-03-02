"use client";
import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Sidebar from "../../components/Sidebar";
import Header from "../../components/Header";
import { audiosAPI, Audio } from "../../lib/api";
import WaveSurfer from "wavesurfer.js";
import Spectrogram from "wavesurfer.js/dist/plugins/spectrogram.esm.js";

export default function AudioDetailsPage() {
    const params = useParams();
    const router = useRouter();
    const id = Number(params.id);
    
    const [audio, setAudio] = useState<Audio | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const originalWaveRef = useRef<HTMLDivElement>(null);
    const originalSpecRef = useRef<HTMLDivElement>(null);
    const processedWaveRef = useRef<HTMLDivElement>(null);
    const processedSpecRef = useRef<HTMLDivElement>(null);

    const [originalWs, setOriginalWs] = useState<WaveSurfer | null>(null);
    const [processedWs, setProcessedWs] = useState<WaveSurfer | null>(null);

    const [isPlayingOriginal, setIsPlayingOriginal] = useState(false);
    const [isPlayingProcessed, setIsPlayingProcessed] = useState(false);

    useEffect(() => {
        if (!id) return;
        
        audiosAPI.get(id)
            .then(res => {
                setAudio(res.audio);
            })
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, [id]);

    useEffect(() => {
        if (!audio || !originalWaveRef.current || !originalSpecRef.current) return;

        const wsOriginal = WaveSurfer.create({
            container: originalWaveRef.current,
            waveColor: '#9ca3af',
            progressColor: '#4b5563',
            height: 60,
            plugins: [
                Spectrogram.create({
                    container: originalSpecRef.current,
                    labels: true,
                    height: 100,
                }),
            ],
        });

        wsOriginal.load(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"}/api/audios/play/${audio.id}?type=original`).catch(err => {
            if (err.name !== 'AbortError') {
                console.error("WaveSurfer load error:", err);
            }
        });
        
        wsOriginal.on('play', () => setIsPlayingOriginal(true));
        wsOriginal.on('pause', () => setIsPlayingOriginal(false));
        
        // Catch fetch errors to prevent unhandled rejections
        wsOriginal.on('error', (err) => {
            console.warn("WaveSurfer original error:", err);
        });
        
        setOriginalWs(wsOriginal);

        return () => {
            try {
                wsOriginal.destroy();
            } catch (e) {
                console.error("Error destroying original wavesurfer:", e);
            }
        };
    }, [audio]);

    useEffect(() => {
        if (!audio || !audio.processed || !processedWaveRef.current || !processedSpecRef.current) return;

        const wsProcessed = WaveSurfer.create({
            container: processedWaveRef.current,
            waveColor: '#3b82f6',
            progressColor: '#1d4ed8',
            height: 60,
            plugins: [
                Spectrogram.create({
                    container: processedSpecRef.current,
                    labels: true,
                    height: 100,
                }),
            ],
        });

        wsProcessed.load(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"}/api/audios/play/${audio.id}?type=processed`).catch(err => {
            if (err.name !== 'AbortError') {
                console.error("WaveSurfer load error:", err);
            }
        });
        
        wsProcessed.on('play', () => setIsPlayingProcessed(true));
        wsProcessed.on('pause', () => setIsPlayingProcessed(false));
        
        // Catch fetch errors to prevent unhandled rejections
        wsProcessed.on('error', (err) => {
            console.warn("WaveSurfer processed error:", err);
        });
        
        setProcessedWs(wsProcessed);

        return () => {
            try {
                wsProcessed.destroy();
            } catch (e) {
                console.error("Error destroying processed wavesurfer:", e);
            }
        };
    }, [audio]);

    if (loading) return <div className="app-layout"><Sidebar /><main className="app-main"><div style={{padding: 40}}>Carregando...</div></main></div>;
    if (error || !audio) return <div className="app-layout"><Sidebar /><main className="app-main"><div style={{padding: 40, color: 'red'}}>{error || "Erro"}</div></main></div>;

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main">
                <Header title="Detalhes do Processamento" subtitle={`Análise do arquivo: ${audio.filename}`} />
                
                <div className="page-content">
                    <button className="btn btn-secondary" onClick={() => router.push('/audios')} style={{ marginBottom: 20 }}>
                        ← Voltar para Lista
                    </button>

                    <div className="stats-grid" style={{ gridTemplateColumns: "repeat(4,1fr)" }}>
                        <div className="stat-card"><div className="stat-icon info">📄</div><div className="stat-body"><div className="stat-label">Tamanho</div><div className="stat-value">{(audio.size_bytes / 1024 / 1024).toFixed(2)} MB</div></div></div>
                        <div className="stat-card"><div className="stat-icon brand">⏱️</div><div className="stat-body"><div className="stat-label">Duração</div><div className="stat-value">{audio.duration_seconds || 0}s</div></div></div>
                        <div className="stat-card"><div className="stat-icon success">✨</div><div className="stat-body"><div className="stat-label">Status</div><div className="stat-value">{audio.processed ? "Processado" : "Pendente"}</div></div></div>
                        <div className="stat-card"><div className="stat-icon warning">📝</div><div className="stat-body"><div className="stat-label">Transcrito</div><div className="stat-value">{audio.transcribed ? "Sim" : "Não"}</div></div></div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginTop: 24 }}>
                        {/* Original Audio */}
                        <div className="card">
                            <div className="card-header">
                                <div className="card-title">Áudio Original (Com Ruído)</div>
                            </div>
                            <div style={{ padding: 20 }}>
                                <button 
                                    className="btn btn-primary" 
                                    onClick={() => originalWs?.playPause()}
                                    style={{ marginBottom: 16 }}
                                >
                                    {isPlayingOriginal ? "⏸ Pausar" : "▶️ Tocar Original"}
                                </button>
                                
                                <div style={{ marginBottom: 8, fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Forma de Onda</div>
                                <div ref={originalWaveRef} style={{ background: '#f3f4f6', borderRadius: 8, overflow: 'hidden', marginBottom: 16 }}></div>
                                
                                <div style={{ marginBottom: 8, fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Espectrograma</div>
                                <div ref={originalSpecRef} style={{ background: '#111827', borderRadius: 8, overflow: 'hidden', minHeight: 100 }}></div>
                            </div>
                        </div>

                        {/* Processed Audio */}
                        <div className="card">
                            <div className="card-header">
                                <div className="card-title">Áudio Processado (IA Denoise)</div>
                            </div>
                            <div style={{ padding: 20 }}>
                                {audio.processed ? (
                                    <>
                                        <button 
                                            className="btn btn-primary" 
                                            onClick={() => processedWs?.playPause()}
                                            style={{ marginBottom: 16, background: 'var(--success)', borderColor: 'var(--success)' }}
                                        >
                                            {isPlayingProcessed ? "⏸ Pausar" : "▶️ Tocar Processado"}
                                        </button>
                                        
                                        <div style={{ marginBottom: 8, fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Forma de Onda</div>
                                        <div ref={processedWaveRef} style={{ background: '#eff6ff', borderRadius: 8, overflow: 'hidden', marginBottom: 16 }}></div>
                                        
                                        <div style={{ marginBottom: 8, fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Espectrograma</div>
                                        <div ref={processedSpecRef} style={{ background: '#111827', borderRadius: 8, overflow: 'hidden', minHeight: 100 }}></div>
                                    </>
                                ) : (
                                    <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
                                        Este áudio ainda não foi processado pela IA.
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Transcription */}
                    <div className="card" style={{ marginTop: 24 }}>
                        <div className="card-header">
                            <div className="card-title">Transcrição (Speech-to-Text)</div>
                        </div>
                        <div style={{ padding: 20 }}>
                            {audio.transcribed ? (
                                <div style={{ 
                                    padding: 20, 
                                    background: 'var(--bg-muted)', 
                                    borderRadius: 8, 
                                    fontSize: 16, 
                                    lineHeight: 1.6,
                                    color: 'var(--text-main)'
                                }}>
                                    {/* @ts-ignore - transcription_text is not in the Audio interface yet, we'll add it */}
                                    {audio.transcription_text || "Texto não disponível."}
                                </div>
                            ) : (
                                <div style={{ color: 'var(--text-muted)' }}>
                                    Nenhuma transcrição disponível para este áudio.
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
