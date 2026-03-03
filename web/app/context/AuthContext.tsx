"use client";
import React, { createContext, useContext, useEffect, useState } from "react";
import { authAPI, User } from "../lib/api";

interface AuthContextType {
    user: User | null;
    loading: boolean;
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
    user: null,
    loading: true,
    login: async () => { },
    logout: () => { },
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem("calmwave_token");
        if (token) {
            authAPI
                .me()
                .then((res) => setUser(res.user))
                .catch(() => localStorage.removeItem("calmwave_token"))
                .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, []);

    const login = async (email: string, password: string) => {
        const res = await authAPI.login(email, password);
        localStorage.setItem("calmwave_token", res.token);
        if (res.refresh_token) {
            localStorage.setItem("calmwave_refresh_token", res.refresh_token);
        }
        setUser(res.user);
    };

    const logout = () => {
        localStorage.removeItem("calmwave_token");
        localStorage.removeItem("calmwave_refresh_token");
        setUser(null);
        window.location.href = "/login";
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);
