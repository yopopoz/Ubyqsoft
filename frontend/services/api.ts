const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

interface FetchOptions extends RequestInit {
    token?: string | null;
}

export class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
        super(message);
        this.status = status;
    }
}

export async function apiFetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
    const { token, headers, ...rest } = options;
    const url = `${API_BASE}${endpoint}`;

    const defaultHeaders: HeadersInit = {
        "Content-Type": "application/json",
    };

    if (token) {
        (defaultHeaders as any)["Authorization"] = `Bearer ${token}`;
    }

    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), 10000); // 10s timeout

    const config: RequestInit = {
        ...rest,
        headers: {
            ...defaultHeaders,
            ...headers,
        },
        signal: controller.signal,
    };

    try {
        const response = await fetch(url, config);
        clearTimeout(id);

        if (!response.ok) {
            if (response.status === 401) {
                // Dispatch global event for AuthContext to handle logout
                if (typeof window !== "undefined") {
                    window.dispatchEvent(new Event("auth:unauthorized"));
                }
                throw new ApiError("Unauthorized", 401);
            }
            const errorData = await response.json().catch(() => ({}));
            throw new ApiError(errorData.detail || "API Error", response.status);
        }

        if (response.status === 204) {
            return {} as T;
        }

        return await response.json();
    } catch (error: any) {
        clearTimeout(id);
        if (error.name === 'AbortError') {
            throw new Error("Délai d'attente dépassé (Timeout). Le serveur ne répond pas.");
        }
        if (error instanceof ApiError) {
            throw error;
        }
        throw new Error(error instanceof Error ? error.message : "Network Error");
    }
}
