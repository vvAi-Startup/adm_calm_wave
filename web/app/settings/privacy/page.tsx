"use client";
import React, { useState } from "react";
import Sidebar from "../../components/Sidebar";
import Header from "../../components/Header";
import { useAuth } from "../../context/AuthContext";

export default function PrivacyPage() {
    const { logout } = useAuth();
    const [loadingExport, setLoadingExport] = useState(false);
    const [loadingDelete, setLoadingDelete] = useState(false);

    const handleExport = async () => {
        setLoadingExport(true);
        try {
            const token = localStorage.getItem("calmwave_token");
            const response = await fetch("http://localhost:5000/api/privacy/export", {
                headers: { "Authorization": `Bearer ${token}` }
            });
            const data = await response.json();

            // Generate standard download link for the JSON Blob
            const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `calmwave_export_${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (e) {
            alert("Falha ao exportar dados.");
        } finally {
            setLoadingExport(false);
        }
    };

    const handleDelete = async () => {
        if (!confirm("Tem certeza que deseja solicitar o Direito ao Esquecimento? Isso apagará TODAS as suas mídias, senhas, acessos e análises de forma PERMANENTE e IRREVERSÍVEL.")) return;

        setLoadingDelete(true);
        try {
            const token = localStorage.getItem("calmwave_token");
            const response = await fetch("http://localhost:5000/api/privacy/delete-account", {
                method: "DELETE",
                headers: { "Authorization": `Bearer ${token}` }
            });

            if (response.ok) {
                alert("Conta excluída de nossos servidores. Adeus!");
                logout();
            } else {
                alert("Falha ao concluir as diretrizes exclusórias.");
            }
        } catch (e) {
            alert("Erro de comunicação.");
        } finally {
            setLoadingDelete(false);
        }
    };

    return (
        <div className="app-layout">
            <Sidebar />
            <main className="app-main">
                <Header title="Privacidade e Controle (LGPD)" subtitle="Nós prezamos pelo seu direito de gerenciar seus rastros digitais" />
                <div className="page-content" style={{ maxWidth: 800 }}>

                    <div className="card" style={{ marginBottom: 24 }}>
                        <div className="card-header">
                            <div className="card-title">Portabilidade de Dados</div>
                        </div>
                        <div style={{ padding: 24 }}>
                            <p className="text-muted" style={{ marginBottom: 16 }}>Você tem o direito de baixar todas as informações de processamento que possuímos a respeito na base de servidores da CalmWave.</p>
                            <button className="btn btn-secondary" onClick={handleExport} disabled={loadingExport}>
                                {loadingExport ? "Gerando Pacote..." : "📥 Baixar Meus Dados (JSON)"}
                            </button>
                        </div>
                    </div>

                    <div className="card border-danger">
                        <div className="card-header bg-danger" style={{ background: "rgba(231, 76, 60, 0.1)" }}>
                            <div className="card-title text-danger">Direito ao Esquecimento</div>
                        </div>
                        <div style={{ padding: 24 }}>
                            <p className="text-muted" style={{ marginBottom: 16 }}>Solicitar o destrato e a exclusão em modo *Cascata Físico* dos seus arquivos. Isso não poderá ser desfeito de forma alguma.</p>
                            <button className="btn btn-danger" onClick={handleDelete} disabled={loadingDelete}>
                                {loadingDelete ? "Acionando Destruição..." : "🗑️ Excluir Minha Conta Permanentemente"}
                            </button>
                        </div>
                    </div>

                </div>
            </main>
        </div>
    );
}

