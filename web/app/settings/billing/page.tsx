"use client";
import { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import Header from "../../components/Header";

interface PlanLimits {
    max_audio_length_seconds: number;
    max_storage_mb: number;
    transcription_included: boolean;
}

export default function BillingPage() {
    const [accountType, setAccountType] = useState<string>("free");
    const [limits, setLimits] = useState<PlanLimits | null>(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);

    const loadPlan = async () => {
        try {
            const token = localStorage.getItem("token");
            const response = await fetch("http://localhost:5000/api/billing/plan", {
                headers: { "Authorization": `Bearer ${token}` }
            });
            const data = await response.json();
            if (data.limits) {
                setAccountType(data.account_type);
                setLimits(data.limits);
            }
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadPlan();
    }, []);

    const changePlan = async (novoPlano: string) => {
        setActionLoading(true);
        try {
            const token = localStorage.getItem("token");
            const response = await fetch("http://localhost:5000/api/billing/upgrade", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ plan: novoPlano })
            });

            if (response.ok) {
                loadPlan();
                alert(`Mudança de plano para ${novoPlano.toUpperCase()} confirmada! Por favor, recarregue a página caso o layout não atualize imediatamente.`);
            } else {
                alert("Falha simulador do gateway.");
            }
        } finally {
            setActionLoading(false);
        }
    };

    if (loading) return null;

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main">
                <Header title="Gerenciar Assinatura" subtitle="Controle a capacidade de armazenamento da conta e uso de APIs neurais" />
                <div className="page-content" style={{ maxWidth: 1000 }}>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 32 }}>
                        {/*  FREE TIER */}
                        <div className="card" style={{ border: accountType === "free" ? "2px solid var(--primary)" : "1px solid var(--border)" }}>
                            <div style={{ padding: 24, textAlign: "center", borderBottom: "1px solid var(--border)" }}>
                                <div style={{ fontSize: 24, fontWeight: "bold", marginBottom: 8 }}>Essencial Gratuito</div>
                                <div className="text-muted" style={{ fontSize: 13, minHeight: 40 }}>Recursos fundamentais pra limpar áudios esporadicamente sem cartão de base.</div>
                                <div style={{ fontSize: 40, fontWeight: 900, marginTop: 16 }}>R$ 0<span style={{ fontSize: 16, color: "var(--text-muted)" }}>/mês</span></div>
                            </div>
                            <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
                                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>✅ Máx. Limpeza 5 minutos / File</div>
                                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>✅ Painel Base de Analytics</div>
                                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>✅ Hospedagem em disco (100 MB)</div>
                                <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--text-muted)", textDecoration: "line-through" }}>❌ Acesso API de Voice-To-Text</div>
                            </div>
                            <div style={{ padding: 24, paddingTop: 0 }}>
                                {accountType === "free" ? (
                                    <button className="btn btn-secondary" style={{ width: "100%" }} disabled>Seu Plano Atual</button>
                                ) : (
                                    <button className="btn btn-secondary" style={{ width: "100%" }} onClick={() => changePlan("free")} disabled={actionLoading}>Downgrade para Free tier (Aviso Restrições)</button>
                                )}
                            </div>
                        </div>

                        {/*  PREMIUM TIER */}
                        <div className="card" style={{ border: accountType === "premium" ? "2px solid var(--brand)" : "1px solid var(--border)", position: "relative", overflow: "hidden" }}>
                            {accountType !== "premium" && <div style={{ position: "absolute", top: 16, right: -30, background: "var(--brand)", color: "#fff", padding: "4px 40px", fontSize: 12, fontWeight: "bold", transform: "rotate(45deg)" }}>RECOMENDADO</div>}
                            <div style={{ padding: 24, textAlign: "center", borderBottom: "1px solid var(--border)", background: accountType === "premium" ? "rgba(10,132,255,0.05)" : "transparent" }}>
                                <div style={{ fontSize: 24, fontWeight: "bold", marginBottom: 8, color: "var(--brand)" }}>Premium Analítica</div>
                                <div className="text-muted" style={{ fontSize: 13, minHeight: 40 }}>Libera os pipelines massivos Pytorch, armazenamento de mídias brutas e suporte técnico expresso.</div>
                                <div style={{ fontSize: 40, fontWeight: 900, marginTop: 16, color: "var(--brand)" }}>R$ 49<span style={{ fontSize: 16, color: "var(--text-muted)" }}>/mês</span></div>
                            </div>
                            <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
                                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>🚀 Máx. Limpeza 60 minutos / File</div>
                                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>🚀 Prioridade na Nuvem de Processamento</div>
                                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>🚀 Hospedagem estendida (5 GBs)</div>
                                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>🤖 Pipeline Completo Voz a Texto</div>
                            </div>
                            <div style={{ padding: 24, paddingTop: 0 }}>
                                {accountType === "premium" ? (
                                    <button className="btn btn-primary" style={{ width: "100%" }} disabled>Plano Ativado ✅</button>
                                ) : (
                                    <button className="btn btn-primary" style={{ width: "100%" }} onClick={() => changePlan("premium")} disabled={actionLoading}>
                                        {actionLoading ? "Processando Cartão..." : "Realizar Upgrade Now"}
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
