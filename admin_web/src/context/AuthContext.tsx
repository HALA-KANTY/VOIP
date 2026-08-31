"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { clearStoredToken, getStoredToken, login as loginRequest, setStoredToken } from "@/lib/api";

interface AuthContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    function verifier() {
      setIsAuthenticated(Boolean(getStoredToken()));
      setIsLoading(false);
    }
    verifier();
  }, []);

  async function login(username: string, password: string) {
    const token = await loginRequest(username, password);
    setStoredToken(token);
    setIsAuthenticated(true);
  }

  function logout() {
    clearStoredToken();
    setIsAuthenticated(false);
    router.push("/login");
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth doit etre utilise a l'interieur de AuthProvider");
  return context;
}
