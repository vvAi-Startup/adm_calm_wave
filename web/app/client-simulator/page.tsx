"use client";
import { useState, useEffect, useRef } from "react";
import { io, Socket } from "socket.io-client";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";

export default function ClientSimulatorPage() {
    const [socket, setSocket] = useState<Socket | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [isStreaming, setIsStreaming] = useState(false);
    const [messagesSent, setMessagesSent] = useState(0);
    const [userName, setUserName] = useState("Usuário Teste");
    const [device, setDevice] = useState("Navegador Web");
    
    const streamIntervalRef = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        const newSocket = io(process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000", {
            path: "/socket.io",
            transports: ["websocket", "polling"]
        });

        setSocket(newSocket);

        newSocket.on("connect", () => {
            setIsConnected(true);
        });

        newSocket.on("disconnect", () => {
            setIsConnected(false);
            setIsStreaming(false);
            if (streamIntervalRef.current) {
                clearInterval(streamIntervalRef.current);
            }
        });

        return () => {
            if (streamIntervalRef.current) {
                clearInterval(streamIntervalRef.current);
            }
            newSocket.disconnect();
        };
    }, []);

    const startStream = () => {
        if (!socket || !isConnected) return;

        socket.emit("start_stream", {
            user: userName,
            device: device
        });

        setIsStreaming(true);
        setMessagesSent(0);

        // Simulador: Criando um cabeçalho WAV falso simplificado para 44.1kHz, mono, 16-bit
        // Apenas para que players e WaveSurfer reconheçam o arquivo como um áudio válido (silêncio/ruído).
        const sampleRate = 44100;
        const numChannels = 1;
        const bitsPerSample = 16;
        
        let headerWritten = false;

        // Simulate sending audio chunks every 500ms
        streamIntervalRef.current = setInterval(() => {
            const dataLength = 16384;
            let chunkData: Uint8Array;
            
            if (!headerWritten) {
                // Escrever o cabeçalho WAV no primeiro chunk
                chunkData = new Uint8Array(44 + dataLength);
                const view = new DataView(chunkData.buffer);
                
                // RIFF
                view.setUint8(0, 'R'.charCodeAt(0)); view.setUint8(1, 'I'.charCodeAt(0)); view.setUint8(2, 'F'.charCodeAt(0)); view.setUint8(3, 'F'.charCodeAt(0));
                view.setUint32(4, 36 + 999999999, true); // Fake huge size
                // WAVE
                view.setUint8(8, 'W'.charCodeAt(0)); view.setUint8(9, 'A'.charCodeAt(0)); view.setUint8(10, 'V'.charCodeAt(0)); view.setUint8(11, 'E'.charCodeAt(0));
                // fmt 
                view.setUint8(12, 'f'.charCodeAt(0)); view.setUint8(13, 'm'.charCodeAt(0)); view.setUint8(14, 't'.charCodeAt(0)); view.setUint8(15, ' '.charCodeAt(0));
                view.setUint32(16, 16, true); // fmt chunk size
                view.setUint16(20, 1, true); // uncompressed
                view.setUint16(22, numChannels, true);
                view.setUint32(24, sampleRate, true);
                view.setUint32(28, sampleRate * numChannels * 2, true); // byte rate
                view.setUint16(32, numChannels * 2, true); // block align
                view.setUint16(34, bitsPerSample, true);
                // data
                view.setUint8(36, 'd'.charCodeAt(0)); view.setUint8(37, 'a'.charCodeAt(0)); view.setUint8(38, 't'.charCodeAt(0)); view.setUint8(39, 'a'.charCodeAt(0));
                view.setUint32(40, 999999999, true); // Fake huge size
                
                // Generate fake binary data (ruído branco) after header
                for (let i = 0; i < dataLength; i++) {
                    chunkData[44 + i] = Math.floor(Math.random() * 256);
                }
                headerWritten = true;
            } else {
                chunkData = new Uint8Array(dataLength);
                for (let i = 0; i < chunkData.length; i++) {
                    chunkData[i] = Math.floor(Math.random() * 256);
                }
            }

            // Convert raw bytes to base64
            let binaryStr = '';
            for(let i = 0; i < chunkData.length; i++) {
                binaryStr += String.fromCharCode(chunkData[i]);
            }
            const base64Data = btoa(binaryStr);
            
            socket.emit("audio_chunk", {
                timestamp: new Date().toISOString(),
                audio_data: base64Data
            });
            setMessagesSent(prev => prev + 1);
        }, 500);
    };

    const stopStream = () => {
        if (!socket || !isConnected) return;

        socket.emit("stop_stream");
        setIsStreaming(false);
        
        if (streamIntervalRef.current) {
            clearInterval(streamIntervalRef.current);
            streamIntervalRef.current = null;
        }
    };

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main">
                <Header title="Simulador de Cliente" subtitle="Simule um dispositivo enviando áudio em tempo real" />
                
                <div className="page-content">
                    <div className="card" style={{ maxWidth: 600, margin: "0 auto" }}>
                        <div className="card-header">
                            <div className="card-title">Controle do Dispositivo Simulado</div>
                            <div className={`badge ${isConnected ? 'badge-success' : 'badge-danger'}`}>
                                <span className="badge-dot" />
                                {isConnected ? 'Conectado ao Servidor' : 'Desconectado'}
                            </div>
                        </div>
                        
                        <div style={{ padding: 20 }}>
                            <div style={{ marginBottom: 16 }}>
                                <label style={{ display: "block", marginBottom: 8, fontWeight: 600, fontSize: 14 }}>Nome do Usuário</label>
                                <input 
                                    type="text" 
                                    className="select" 
                                    style={{ width: "100%", padding: "8px 12px" }}
                                    value={userName}
                                    onChange={(e) => setUserName(e.target.value)}
                                    disabled={isStreaming}
                                />
                            </div>
                            
                            <div style={{ marginBottom: 24 }}>
                                <label style={{ display: "block", marginBottom: 8, fontWeight: 600, fontSize: 14 }}>Dispositivo</label>
                                <input 
                                    type="text" 
                                    className="select" 
                                    style={{ width: "100%", padding: "8px 12px" }}
                                    value={device}
                                    onChange={(e) => setDevice(e.target.value)}
                                    disabled={isStreaming}
                                />
                            </div>

                            <div style={{ display: "flex", gap: 12, alignItems: "center", padding: 20, background: "var(--bg-muted)", borderRadius: 8 }}>
                                {!isStreaming ? (
                                    <button 
                                        className="btn btn-primary" 
                                        onClick={startStream}
                                        disabled={!isConnected}
                                        style={{ flex: 1, background: "var(--success)", borderColor: "var(--success)" }}
                                    >
                                        ▶️ Iniciar Gravação (Streaming)
                                    </button>
                                ) : (
                                    <button 
                                        className="btn btn-primary" 
                                        onClick={stopStream}
                                        style={{ flex: 1, background: "var(--danger)", borderColor: "var(--danger)" }}
                                    >
                                        ⏹️ Parar Gravação
                                    </button>
                                )}
                            </div>

                            {isStreaming && (
                                <div style={{ marginTop: 24, textAlign: "center" }}>
                                    <div style={{ fontSize: 48, marginBottom: 8 }}>🎙️</div>
                                    <div style={{ fontSize: 18, fontWeight: 600, color: "var(--brand)" }}>Enviando áudio ao vivo...</div>
                                    <div style={{ color: "var(--text-muted)", marginTop: 8 }}>
                                        Pacotes enviados: <strong>{messagesSent}</strong>
                                    </div>
                                    
                                    {/* Fake waveform animation */}
                                    <div className="waveform" style={{ height: 40, marginTop: 20, justifyContent: "center" }}>
                                        {Array.from({ length: 20 }).map((_, i) => (
                                            <div
                                                key={i}
                                                className="wave-bar played"
                                                style={{ 
                                                    height: `${20 + Math.random() * 80}%`, 
                                                    animation: `pulse ${0.5 + Math.random()}s infinite alternate` 
                                                }}
                                            />
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                    
                    <div style={{ marginTop: 24, textAlign: "center", color: "var(--text-muted)", fontSize: 14 }}>
                        <p>Abra a página de <strong>Streaming</strong> em outra aba para ver esta sessão aparecendo em tempo real!</p>
                    </div>
                </div>
            </main>
            
            <style dangerouslySetInnerHTML={{__html: `
                @keyframes pulse {
                    0% { opacity: 0.4; transform: scaleY(0.8); }
                    100% { opacity: 1; transform: scaleY(1.2); }
                }
            `}} />
        </div>
    );
}
