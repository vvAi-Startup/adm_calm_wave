"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
    const { login } = useAuth();
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            await login(email, password);
            router.push("/dashboard");
        } catch {
            setError("Email ou senha inválidos.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-page">
            <div className="login-left">
                <div className="login-box">
                    <div className="login-logo-wrap">
                        <div className="login-logo">
                            <div className="login-logo-icon">🌊</div>
                            <span className="login-logo-name">CALM WAVE</span>
                        </div>
                    </div>

                    <div className="login-title">Bem-vindo de volta</div>
                    <div className="login-subtitle">Faça login no painel de controle</div>

                    <div className="login-form-wrap">
                        {error && <div className="login-error">{error}</div>}
                        <form onSubmit={handleSubmit}>
                            <div className="form-group">
                                <label className="form-label" htmlFor="email">Usuário (Email)</label>
                                <input
                                    id="email"
                                    type="email"
                                    className="input"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="seu@email.com"
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label" htmlFor="password">Senha</label>
                                <input
                                    id="password"
                                    type="password"
                                    className="input"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                            <button
                                type="submit"
                                className="login-submit"
                                disabled={loading}
                            >
                                {loading ? "Entrando..." : "Entrar"}
                            </button>
                        </form>

                    </div>
                </div>
            </div>

            <div className="login-right">
                <div className="login-hero">
                    <div className="login-hero-icon">🌊</div>
                    <div className="login-hero-title">Calm Wave Admin</div>
                    <div className="login-hero-desc">
                        Gerencie usuários, áudios e análises<br />
                        de forma simples e poderosa.
                    </div>
                </div>
            </div>
        </div>
    );
}
