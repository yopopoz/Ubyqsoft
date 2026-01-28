"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";

interface AuthContextType {
  user: any;
  token: string | null;
  login: (token: string) => void;
  logout: () => void;
  isLoading: boolean;
  // Role helpers
  isOps: boolean;
  isAdmin: boolean;
  canWrite: boolean;  // ops or admin
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  login: () => { },
  logout: () => { },
  isLoading: true,
  isOps: false,
  isAdmin: false,
  canWrite: false,
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<any>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  // Helper to decode JWT safely
  const decodeToken = (token: string) => {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(function (c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(''));
      return JSON.parse(jsonPayload);
    } catch (e) {
      console.error("Failed to decode token", e);
      return null;
    }
  };

  const login = (newToken: string) => {
    localStorage.setItem("token", newToken);
    setToken(newToken);
    const payload = decodeToken(newToken);
    if (payload) {
      setUser(payload);
      router.push("/");
    } else {
      // If decoding fails, maybe just push anyway? Or clear?
      // Let's assume valid token for now but handle error gracefully
      console.error("Login failed: invalid token format");
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
    router.push("/login");
  };

  useEffect(() => {
    // Check localStorage for token
    const storedToken = localStorage.getItem("token");
    if (storedToken) {
      setToken(storedToken);
      const payload = decodeToken(storedToken);
      if (payload) {
        setUser(payload);
      } else {
        localStorage.removeItem("token");
        setToken(null);
      }
    }
    setIsLoading(false);

    // Listen for 401 Unauthorized events from api.ts
    const handleUnauthorized = () => {
      logout();
    };
    window.addEventListener("auth:unauthorized", handleUnauthorized);

    return () => {
      window.removeEventListener("auth:unauthorized", handleUnauthorized);
    };
  }, []);



  // Protected route logic
  useEffect(() => {
    if (!isLoading && !token && pathname !== "/login") {
      router.push("/login");
    }
  }, [isLoading, token, pathname, router]);

  // Role helpers (computed)
  const role = user?.role || "client";
  const isOps = role === "ops";
  const isAdmin = role === "admin";
  const canWrite = role === "ops" || role === "admin";

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading, isOps, isAdmin, canWrite }}>
      {children}
    </AuthContext.Provider>
  );
};
