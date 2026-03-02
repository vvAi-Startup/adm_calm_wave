"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "../context/AuthContext";

const navItems = [
    { href: "/dashboard", icon: "📊", label: "Dashboard", section: "Visão Geral" },
    { href: "/audios", icon: "🎙️", label: "Áudios", section: "Conteúdo" },
    { href: "/streaming", icon: "📡", label: "Streaming", section: "Conteúdo" },
    { href: "/client-simulator", icon: "📱", label: "Simulador App", section: "Conteúdo" },
    { href: "/users", icon: "👥", label: "Usuários", section: "Administração" },
    { href: "/analytics", icon: "📈", label: "Analytics", section: "Administração" },
    { href: "/status", icon: "🖥️", label: "Status", section: "Administração" },
    { href: "/logs", icon: "📋", label: "Logs", section: "Administração" },
    { href: "/achievements", icon: "🏆", label: "Conquistas", section: "Usuário" },
    { href: "/settings", icon: "⚙️", label: "Configurações", section: "Usuário" },
    { href: "/privacy", icon: "🔒", label: "Privacidade", section: "Usuário" },
];

const sections = ["Visão Geral", "Conteúdo", "Administração", "Usuário"];

export default function Sidebar() {
    const pathname = usePathname();
    const { user, logout } = useAuth();

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <div className="sidebar-logo-icon">🌊</div>
                <div>
                    <div className="sidebar-logo-text">Calm Wave</div>
                    <div className="sidebar-logo-sub">Admin Console</div>
                </div>
            </div>

            {sections.map((section) => {
                const items = navItems.filter((i) => i.section === section);
                return (
                    <div key={section} className="sidebar-section">
                        <div className="sidebar-section-label">{section}</div>
                        {items.map((item) => (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={`sidebar-link ${pathname === item.href ? "active" : ""}`}
                            >
                                <span className="sidebar-link-icon">{item.icon}</span>
                                {item.label}
                            </Link>
                        ))}
                    </div>
                );
            })}

            <div className="sidebar-footer">
                <div className="sidebar-user" onClick={logout} title="Sair">
                    <div className="sidebar-avatar">
                        {user?.name?.charAt(0).toUpperCase() ?? "A"}
                    </div>
                    <div className="sidebar-user-info">
                        <div className="sidebar-user-name">{user?.name ?? "Admin"}</div>
                        <div className="sidebar-user-role">{user?.account_type ?? "admin"} · Sair</div>
                    </div>
                </div>
            </div>
        </aside>
    );
}
