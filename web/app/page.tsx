"use client";
import { redirect } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "./context/AuthContext";

export default function Home() {
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading) {
      if (user) {
        window.location.href = "/dashboard";
      } else {
        window.location.href = "/login";
      }
    }
  }, [user, loading]);

  return null;
}
