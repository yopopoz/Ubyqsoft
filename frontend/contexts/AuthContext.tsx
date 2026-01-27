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

  const login = (newToken: string) => {
    localStorage.setItem("token", newToken);
    setToken(newToken);
    const payload = JSON.parse(atob(newToken.split(".")[1]));
    setUser(payload);
    router.push("/");
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
      // Decode token for user info (simple version)
      try {
        const payload = JSON.parse(atob(storedToken.split(".")[1]));
        setUser(payload);
      } catch (e) {
        console.error("Invalid token", e);
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
