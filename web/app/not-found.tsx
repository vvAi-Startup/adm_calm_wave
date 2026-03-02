"use client";
import { useRouter } from "next/navigation";

export default function NotFound() {
    const router = useRouter();
    return (
        <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg-base)", flexDirection: "column", gap: 24, textAlign: "center", padding: 32 }}>
            <div style={{ fontSize: 80 }}>🌊</div>
            <div>
                <div style={{ fontSize: 96, fontWeight: 900, color: "var(--brand)", lineHeight: 1 }}>404</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)", marginTop: 8 }}>Página não encontrada</div>
                <div style={{ fontSize: 15, color: "var(--text-secondary)", marginTop: 8, maxWidth: 360 }}>
                    Esta página não existe ou foi movida. Volte ao dashboard para continuar.
                </div>
            </div>
            <div style={{ display: "flex", gap: 12 }}>
                <button className="btn btn-primary" onClick={() => router.push("/dashboard")}>Ir para o Dashboard</button>
                <button className="btn btn-secondary" onClick={() => router.back()}>← Voltar</button>
            </div>
        </div>
    );
}
