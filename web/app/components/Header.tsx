"use client";



import { useState, useEffect, useRef } from "react";

import { notificationsAPI, Notification } from "../lib/api";



interface HeaderProps {

    title: string;

    subtitle?: string;

    status?: "online" | "offline";

}



export default function Header({ title, subtitle, status = "online" }: HeaderProps) {

    const [notifications, setNotifications] = useState<Notification[]>([]);

    const [showDropdown, setShowDropdown] = useState(false);

    const dropdownRef = useRef<HTMLDivElement>(null);



    useEffect(() => {

        loadNotifications();

        

        // Simulating polling or we could use socket.io later

        const interval = setInterval(loadNotifications, 30000);

        

        const handleClickOutside = (event: MouseEvent) => {

            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {

                setShowDropdown(false);

            }

        };

        document.addEventListener("mousedown", handleClickOutside);

        

        return () => {

            clearInterval(interval);

            document.removeEventListener("mousedown", handleClickOutside);

        };

    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);



    const loadNotifications = async () => {

        try {

            const data = await notificationsAPI.list();

            setNotifications(data);

        } catch (error) {

            console.error("Failed to load notifications", error);

        }

    };



    const handleMarkRead = async (id: number) => {

        try {

            await notificationsAPI.markRead(id);

            setNotifications(notifications.map(n => n.id === id ? { ...n, is_read: true } : n));

        } catch (error) {

            console.error(error);

        }

    };



    const handleMarkAllRead = async () => {

        try {

            await notificationsAPI.markAllRead();

            setNotifications(notifications.map(n => ({ ...n, is_read: true })));

        } catch (error) {

            console.error(error);

        }

    };



    const unreadCount = notifications.filter(n => !n.is_read).length;



    return (

        <header className="header">

            <div>

                <div className="header-title">{title}</div>

                {subtitle && <div className="header-subtitle">{subtitle}</div>}

            </div>

            <div className="header-right" style={{ display: "flex", alignItems: "center", gap: "20px" }}>

                

                {/* Notifications Dropdown */}

                <div ref={dropdownRef} style={{ position: "relative" }}>

                    <button 

                        onClick={() => setShowDropdown(!showDropdown)}

                        style={{ 

                            background: "none", border: "none", cursor: "pointer", 

                            fontSize: "20px", position: "relative", padding: "8px" 

                        }}

                    >

                        🔔

                        {unreadCount > 0 && (

                            <span style={{

                                position: "absolute", top: 0, right: 0, background: "var(--danger)",

                                color: "white", fontSize: "10px", fontWeight: "bold",

                                borderRadius: "50%", minWidth: "18px", height: "18px",

                                display: "flex", alignItems: "center", justifyContent: "center"

                            }}>

                                {unreadCount}

                            </span>

                        )}

                    </button>



                    {showDropdown && (

                        <div style={{

                            position: "absolute", top: "100%", right: 0, marginTop: "8px",

                            width: "320px", background: "var(--bg-surface, #ffffff)", border: "1px solid var(--border)",

                            borderRadius: "8px", boxShadow: "0 10px 25px rgba(0,0,0,0.2)",

                            zIndex: 100, overflow: "hidden", display: "flex", flexDirection: "column"

                        }}>

                            <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>

                                <span style={{ fontWeight: 600, fontSize: "14px" }}>Notificações</span>

                                {unreadCount > 0 && (

                                    <button onClick={handleMarkAllRead} style={{ fontSize: "12px", background: "none", border: "none", color: "var(--brand-main)", cursor: "pointer" }}>

                                        Marcar todas como lidas

                                    </button>

                                )}

                            </div>

                            

                            <div style={{ maxHeight: "300px", overflowY: "auto", display: "flex", flexDirection: "column" }}>

                                {notifications.length === 0 ? (

                                    <div style={{ padding: "24px", textAlign: "center", color: "var(--text-muted)", fontSize: "13px" }}>

                                        Nenhuma notificação por enquanto.

                                    </div>

                                ) : (

                                    notifications.map(n => (

                                        <div 

                                            key={n.id} 

                                            onClick={() => !n.is_read && handleMarkRead(n.id)}

                                            style={{ 

                                                padding: "12px 16px", 

                                                borderBottom: "1px solid var(--border)",

                                                background: n.is_read ? "transparent" : "var(--card-hover)",

                                                cursor: n.is_read ? "default" : "pointer",

                                                display: "flex", gap: "12px"

                                            }}

                                        >

                                            <div style={{ fontSize: "16px", marginTop: "2px" }}>

                                                {n.type === "success" ? "✅" : n.type === "warning" ? "⚠️" : n.type === "danger" ? "🚨" : "ℹ️"}

                                            </div>

                                            <div style={{ flex: 1 }}>

                                                <div style={{ fontSize: "13px", fontWeight: n.is_read ? 500 : 700, color: "var(--text-main)" }}>

                                                    {n.title}

                                                </div>

                                                <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>

                                                    {n.message}

                                                </div>

                                                <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "6px" }}>

                                                    {new Date(n.created_at).toLocaleString('pt-BR')}

                                                </div>

                                            </div>

                                            {!n.is_read && (

                                                <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--brand-main)", marginTop: "6px" }} />

                                            )}

                                        </div>

                                    ))

                                )}

                            </div>

                        </div>

                    )}

                </div>



                <div className="header-badge">

                    <span className="header-badge-dot" style={{ background: status === "online" ? "#10b981" : "#ef4444" }} />

                    {status === "online" ? "Sistema Operacional" : "Sistema Indisponível"}

                </div>

            </div>

        </header>

    );

}

