"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { io, Socket } from "socket.io-client";
import toast from "react-hot-toast";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

interface Room {
  id: number;
  name: string;
  room_code: string;
  is_active: boolean;
  host_user_id: number | null;
  created_at: string;
}

interface Participant {
  username: string;
  role: "host" | "listener";
  socket_id?: string;
}

type ViewState = "lobby" | "create" | "join" | "room";

export default function RoomsPage() {
  const [view, setView] = useState<ViewState>("lobby");
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);

  // Formulários
  const [newRoomName, setNewRoomName] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [username, setUsername] = useState("");

  // Estado da sala ativa
  const [activeRoom, setActiveRoom] = useState<Room | null>(null);
  const [myRole, setMyRole] = useState<"host" | "listener">("listener");
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [transcription, setTranscription] = useState<string | null>(null);
  const [processedUrl, setProcessedUrl] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [chunkCount, setChunkCount] = useState(0);

  // WebSocket
  const socketRef = useRef<Socket | null>(null);

  // Áudio (host)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Áudio (listener) — MediaSource API para streaming WebM incremental
  const audioElRef = useRef<HTMLAudioElement | null>(null);
  const mediaSourceRef = useRef<MediaSource | null>(null);
  const sourceBufferRef = useRef<SourceBuffer | null>(null);
  const chunkQueueRef = useRef<ArrayBuffer[]>([]);
  const msReadyRef = useRef(false);

  // ─── Fetch salas ──────────────────────────────────────────────────────────

  const fetchRooms = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/rooms`);
      const data = await res.json();
      setRooms(data.rooms || []);
    } catch {
      toast.error("Erro ao carregar salas");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRooms();
  }, [fetchRooms]);

  // ─── Reprodução de áudio (listener) via MediaSource API ─────────────────

  const flushChunkQueue = useCallback(() => {
    const sb = sourceBufferRef.current;
    if (!sb || !msReadyRef.current) return;
    while (chunkQueueRef.current.length > 0 && !sb.updating) {
      const nextChunk = chunkQueueRef.current[0];
      if (!nextChunk) break;

      try {
        sb.appendBuffer(nextChunk);
        chunkQueueRef.current.shift();
      } catch (error) {
        if (error instanceof DOMException) {
          if (error.name === "QuotaExceededError") {
            // Buffer cheio temporariamente: mantém o chunk na fila para tentar novamente depois.
            break;
          }

          if (error.name === "InvalidStateError") {
            // SourceBuffer/MediaSource ainda não está pronto para append: preserva a fila.
            break;
          }
        }

        console.error("Erro ao anexar chunk de áudio ao SourceBuffer:", error);
        break;
      }
    }
  }, []);

  const initListenerAudio = useCallback(() => {
    const audio = audioElRef.current;
    if (!audio || mediaSourceRef.current) return;

    const ms = new MediaSource();
    mediaSourceRef.current = ms;
    audio.src = URL.createObjectURL(ms);

    ms.addEventListener("sourceopen", () => {
      try {
        const mime = 'audio/webm; codecs="opus"';
        const sb = ms.addSourceBuffer(mime);
        sourceBufferRef.current = sb;

        sb.addEventListener("updateend", () => {
          flushChunkQueue();
        });

        msReadyRef.current = true;
        flushChunkQueue(); // drena chunks que chegaram antes do sourceopen
      } catch (e) {
        console.error("MediaSource init error:", e);
      }
    });

    audio.play().catch(() => {});
  }, [flushChunkQueue]);

  // ─── Parar stream (host) ──────────────────────────────────────────────────

  const stopStreaming = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    mediaRecorderRef.current = null;
    setIsStreaming(false);
  }, []);

  // ─── Sair da sala ─────────────────────────────────────────────────────────

  const leaveRoom = useCallback(() => {
    if (activeRoom) {
      socketRef.current?.emit("leave_room_session", { room_code: activeRoom.room_code });
    }
    stopStreaming();

    // Limpa MediaSource do listener
    if (mediaSourceRef.current && mediaSourceRef.current.readyState === "open") {
      try { mediaSourceRef.current.endOfStream(); } catch {}
    }
    mediaSourceRef.current = null;
    sourceBufferRef.current = null;
    chunkQueueRef.current = [];
    msReadyRef.current = false;
    if (audioElRef.current) audioElRef.current.src = "";

    setView("lobby");
    setActiveRoom(null);
    setParticipants([]);
    setIsStreaming(false);
    setTranscription(null);
    setProcessedUrl(null);
  }, [activeRoom, stopStreaming]);

  // ─── Socket ───────────────────────────────────────────────────────────────

  useEffect(() => {
    const socket = io(API_URL, {
      path: "/socket.io",
      transports: ["websocket", "polling"],
    });
    socketRef.current = socket;

    socket.on("room_joined", (data) => {
      setMyRole(data.role);
      if (data.participants) {
        setParticipants(data.participants);
      }
      setView("room");
      if (data.role === "listener") {
        // Inicializa MediaSource após interação do usuário (clique em "Entrar")
        setTimeout(() => initListenerAudio(), 100);
      }
    });

    socket.on("room_participant_joined", (data: Participant & { room_code: string }) => {
      setParticipants((prev) => {
        if (prev.some((p) => p.socket_id === data.socket_id)) return prev;
        return [...prev, { username: data.username, role: data.role, socket_id: data.socket_id }];
      });
      toast(`${data.username} entrou na sala`, { icon: "👤" });
    });

    socket.on("room_participant_left", (data: { socket_id: string }) => {
      setParticipants((prev) => prev.filter((p) => p.socket_id !== data.socket_id));
    });

    socket.on("room_audio_chunk", (data: { audio_data: string; chunk_index: number }) => {
      if (!data.audio_data) return;
      try {
        const binary = atob(data.audio_data);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
        const buf = bytes.buffer;

        if (sourceBufferRef.current && msReadyRef.current && !sourceBufferRef.current.updating) {
          sourceBufferRef.current.appendBuffer(buf);
        } else {
          chunkQueueRef.current.push(buf);
        }
      } catch {
        // chunk malformado — ignora
      }
    });

    socket.on("room_stream_processing", () => {
      setProcessing(true);
      setIsStreaming(false);
      toast("Processando áudio com IA...", { icon: "⚙️" });
    });

    socket.on("room_audio_completed", (data) => {
      setProcessing(false);
      setTranscription(data.transcription || null);
      setProcessedUrl(data.processed_url || null);
      toast.success("Áudio processado e disponível!");
    });

    socket.on("room_closed", () => {
      toast.error("A sala foi encerrada pelo host.");
      leaveRoom();
    });

    socket.on("room_error", (data: { message: string }) => {
      toast.error(data.message);
    });

    return () => {
      socket.disconnect();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initListenerAudio, leaveRoom]);

  // ─── Criar sala ───────────────────────────────────────────────────────────

  const handleCreateRoom = async () => {
    if (!newRoomName.trim() || !username.trim()) {
      toast.error("Preencha o nome da sala e seu nome");
      return;
    }
    try {
      const res = await fetch(`${API_URL}/api/rooms`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newRoomName }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);

      const room: Room = data.room;
      setActiveRoom(room);
      setParticipants([]);
      setTranscription(null);
      setProcessedUrl(null);
      setChunkCount(0);

      socketRef.current?.emit("join_room_as_host", {
        room_code: room.room_code,
        user: username,
        device: "Web Browser",
      });

      await fetchRooms();
    } catch (e: unknown) {
      toast.error((e as Error).message || "Erro ao criar sala");
    }
  };

  // ─── Entrar na sala ───────────────────────────────────────────────────────

  const handleJoinRoom = async () => {
    if (!joinCode.trim() || !username.trim()) {
      toast.error("Preencha o código da sala e seu nome");
      return;
    }
    try {
      const res = await fetch(`${API_URL}/api/rooms/${joinCode.toUpperCase()}`);
      if (!res.ok) throw new Error("Sala não encontrada");
      const data = await res.json();
      setActiveRoom(data.room);
      setParticipants(data.participants || []);
      setTranscription(null);
      setProcessedUrl(null);
      setChunkCount(0);

      socketRef.current?.emit("join_room_as_listener", {
        room_code: joinCode.toUpperCase(),
        user: username,
      });
    } catch (e: unknown) {
      toast.error((e as Error).message || "Sala não encontrada");
    }
  };

  // ─── Iniciar stream (host) ────────────────────────────────────────────────

  const startStreaming = async () => {
    if (!activeRoom) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mimeType = "audio/wav";
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        stream.getTracks().forEach((track) => track.stop());
        toast.error("Seu navegador não suporta gravação em WAV");
        return;
      }

      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0 && socketRef.current) {
          const reader = new FileReader();
          reader.onloadend = () => {
            const base64 = (reader.result as string).split(",")[1];
            socketRef.current!.emit("audio_chunk_room", {
              room_code: activeRoom.room_code,
              audio_data: base64,
            });
            setChunkCount((c) => c + 1);
          };
          reader.readAsDataURL(event.data);
        }
      };

      recorder.start(500); // chunk a cada 500ms
      setIsStreaming(true);
      toast.success("Transmissão iniciada!");
    } catch {
      toast.error("Não foi possível acessar o microfone");
    }
  };

  const handleStopStream = () => {
    if (!activeRoom) return;
    stopStreaming();
    socketRef.current?.emit("stop_room_stream", { room_code: activeRoom.room_code });
    setProcessing(true);
  };

  // ─── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="app-main">
        <Header title="Salas de Áudio" subtitle="Transmita áudio para múltiplos ouvintes em tempo real" />
        <div className="page-content">

          {/* LOBBY */}
          {view === "lobby" && (
            <>
              <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
                <button className="btn btn-primary" onClick={() => setView("create")}>
                  + Criar Sala
                </button>
                <button className="btn btn-secondary" onClick={() => setView("join")}>
                  Entrar em Sala
                </button>
              </div>

              <div className="card">
                <div className="card-header">
                  <div className="card-title">Salas Ativas</div>
                  <button className="btn-icon" onClick={fetchRooms} title="Atualizar">↻</button>
                </div>
                {loading ? (
                  <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
                    Carregando...
                  </div>
                ) : rooms.length === 0 ? (
                  <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
                    Nenhuma sala ativa. Crie uma para começar.
                  </div>
                ) : (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Código</th>
                          <th>Nome</th>
                          <th>Criada em</th>
                          <th>Ações</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rooms.map((r) => (
                          <tr key={r.id}>
                            <td>
                              <code style={{ fontSize: 13, background: "var(--bg-muted)", padding: "2px 8px", borderRadius: 4, letterSpacing: 2 }}>
                                {r.room_code}
                              </code>
                            </td>
                            <td style={{ fontWeight: 600 }}>{r.name}</td>
                            <td className="text-muted">{new Date(r.created_at).toLocaleString("pt-BR")}</td>
                            <td>
                              <button
                                className="btn btn-secondary"
                                style={{ padding: "4px 12px", fontSize: 13 }}
                                onClick={() => {
                                  setJoinCode(r.room_code);
                                  setView("join");
                                }}
                              >
                                Entrar
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}

          {/* CRIAR SALA */}
          {view === "create" && (
            <div className="card" style={{ maxWidth: 480 }}>
              <div className="card-header">
                <div className="card-title">Nova Sala</div>
                <button className="btn-icon" onClick={() => setView("lobby")}>✕</button>
              </div>
              <div style={{ padding: "0 4px 16px", display: "flex", flexDirection: "column", gap: 14 }}>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, display: "block", marginBottom: 6 }}>Seu nome</label>
                  <input
                    className="input"
                    placeholder="Ex: João Silva"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, display: "block", marginBottom: 6 }}>Nome da sala</label>
                  <input
                    className="input"
                    placeholder="Ex: Reunião de hoje"
                    value={newRoomName}
                    onChange={(e) => setNewRoomName(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleCreateRoom()}
                  />
                </div>
                <div style={{ display: "flex", gap: 10, marginTop: 4 }}>
                  <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleCreateRoom}>
                    Criar e Entrar
                  </button>
                  <button className="btn btn-secondary" onClick={() => setView("lobby")}>Cancelar</button>
                </div>
              </div>
            </div>
          )}

          {/* ENTRAR EM SALA */}
          {view === "join" && (
            <div className="card" style={{ maxWidth: 480 }}>
              <div className="card-header">
                <div className="card-title">Entrar em Sala</div>
                <button className="btn-icon" onClick={() => setView("lobby")}>✕</button>
              </div>
              <div style={{ padding: "0 4px 16px", display: "flex", flexDirection: "column", gap: 14 }}>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, display: "block", marginBottom: 6 }}>Seu nome</label>
                  <input
                    className="input"
                    placeholder="Ex: Maria Costa"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, display: "block", marginBottom: 6 }}>Código da sala</label>
                  <input
                    className="input"
                    placeholder="Ex: ABC123"
                    value={joinCode}
                    onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                    maxLength={6}
                    style={{ letterSpacing: 4, fontWeight: 700, fontSize: 18 }}
                    onKeyDown={(e) => e.key === "Enter" && handleJoinRoom()}
                  />
                </div>
                <div style={{ display: "flex", gap: 10, marginTop: 4 }}>
                  <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleJoinRoom}>
                    Entrar
                  </button>
                  <button className="btn btn-secondary" onClick={() => setView("lobby")}>Cancelar</button>
                </div>
              </div>
            </div>
          )}

          {/* SALA ATIVA */}
          {view === "room" && activeRoom && (
            <>
              {/* Header da sala */}
              <div className="card" style={{ marginBottom: 16 }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
                  <div>
                    <div style={{ fontSize: 20, fontWeight: 700 }}>{activeRoom.name}</div>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 4 }}>
                      <code style={{ fontSize: 16, background: "var(--bg-muted)", padding: "3px 10px", borderRadius: 6, letterSpacing: 3, fontWeight: 700 }}>
                        {activeRoom.room_code}
                      </code>
                      <span className={`badge ${myRole === "host" ? "badge-warning" : "badge-success"}`}>
                        <span className="badge-dot" />
                        {myRole === "host" ? "Host" : "Ouvinte"}
                      </span>
                      {isStreaming && (
                        <span className="badge badge-danger">
                          <span className="badge-dot" />
                          Ao Vivo
                        </span>
                      )}
                    </div>
                  </div>
                  <button className="btn btn-secondary" onClick={leaveRoom}>Sair da Sala</button>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                {/* Painel do host */}
                {myRole === "host" && (
                  <div className="card">
                    <div className="card-header">
                      <div className="card-title">Transmissão de Áudio</div>
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 16, paddingBottom: 8 }}>
                      {/* Waveform visual */}
                      <div style={{ background: "var(--bg-muted)", borderRadius: "var(--radius)", padding: 16 }}>
                        <div className="waveform" style={{ height: 60 }}>
                          {Array.from({ length: 40 }).map((_, i) => (
                            <div
                              key={i}
                              className={`wave-bar ${isStreaming ? "played" : ""}`}
                              style={{
                                height: isStreaming
                                  ? `${20 + Math.abs(Math.sin((i + chunkCount) * 0.5)) * 60}%`
                                  : "20%",
                                opacity: isStreaming ? 0.8 : 0.3,
                                transition: "height 0.3s ease",
                              }}
                            />
                          ))}
                        </div>
                        <div style={{ textAlign: "center", fontSize: 12, color: "var(--text-muted)", marginTop: 8 }}>
                          {isStreaming ? `Transmitindo... ${chunkCount} chunks enviados` : "Pronto para transmitir"}
                        </div>
                      </div>

                      {processing ? (
                        <div style={{ textAlign: "center", padding: "16px 0", color: "var(--text-secondary)" }}>
                          ⚙️ Processando com IA...
                        </div>
                      ) : (
                        <div style={{ display: "flex", gap: 10 }}>
                          {!isStreaming ? (
                            <button className="btn btn-primary" style={{ flex: 1 }} onClick={startStreaming}>
                              🎙️ Iniciar Transmissão
                            </button>
                          ) : (
                            <button
                              className="btn"
                              style={{ flex: 1, background: "var(--danger)", color: "#fff" }}
                              onClick={handleStopStream}
                            >
                              ⏹ Parar e Processar
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Painel do listener */}
                {myRole === "listener" && (
                  <div className="card">
                    <div className="card-header">
                      <div className="card-title">Áudio ao Vivo</div>
                    </div>
                    <div style={{ padding: "8px 0" }}>
                      {/* Elemento de áudio oculto — alimentado pelo MediaSource */}
                      <audio ref={audioElRef} style={{ display: "none" }} />

                      <div style={{ background: "var(--bg-muted)", borderRadius: "var(--radius)", padding: 16, marginBottom: 16 }}>
                        <div className="waveform" style={{ height: 60 }}>
                          {Array.from({ length: 40 }).map((_, i) => (
                            <div
                              key={i}
                              className="wave-bar played"
                              style={{
                                height: `${15 + Math.abs(Math.sin(i * 0.4)) * 55}%`,
                                opacity: 0.5,
                              }}
                            />
                          ))}
                        </div>
                        <div style={{ textAlign: "center", fontSize: 12, color: "var(--text-muted)", marginTop: 8 }}>
                          {msReadyRef.current ? "Recebendo áudio do host..." : "Aguardando transmissão do host..."}
                        </div>
                      </div>
                      {processing && (
                        <div style={{ textAlign: "center", color: "var(--text-secondary)" }}>
                          ⚙️ Host encerrou — processando com IA...
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Participantes */}
                <div className="card">
                  <div className="card-header">
                    <div className="card-title">Participantes ({participants.length})</div>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8, paddingBottom: 8 }}>
                    {participants.length === 0 ? (
                      <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Nenhum participante ainda.</div>
                    ) : (
                      participants.map((p, idx) => (
                        <div key={idx} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <div style={{
                            width: 32, height: 32, borderRadius: "50%",
                            background: p.role === "host" ? "var(--warning)" : "var(--brand)",
                            display: "flex", alignItems: "center", justifyContent: "center",
                            color: "#fff", fontWeight: 700, fontSize: 13,
                          }}>
                            {p.username.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <div style={{ fontWeight: 600, fontSize: 14 }}>{p.username}</div>
                            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                              {p.role === "host" ? "🎙️ Host" : "🎧 Ouvinte"}
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>

              {/* Resultado do processamento */}
              {(transcription || processedUrl) && (
                <div className="card" style={{ marginTop: 16 }}>
                  <div className="card-header">
                    <div className="card-title">Resultado do Processamento</div>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 16, paddingBottom: 8 }}>
                    {processedUrl && (
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Áudio processado (sem ruído):</div>
                        <audio controls style={{ width: "100%" }} src={processedUrl} />
                      </div>
                    )}
                    {transcription && (
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Transcrição:</div>
                        <div style={{
                          background: "var(--bg-muted)", borderRadius: "var(--radius)",
                          padding: 14, fontSize: 14, lineHeight: 1.6,
                        }}>
                          {transcription}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
