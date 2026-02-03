"use client";

import { useState, useRef, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";

export default function Chatbot() {
    const { token } = useAuth();
    const [isOpen, setIsOpen] = useState(false);
    const [message, setMessage] = useState("");
    const [messages, setMessages] = useState<{ role: string; content: string }[]>([
        { role: "assistant", content: "Bonjour ! Je suis votre assistant logistique PURE TRADE. Comment puis-je vous aider aujourd'hui ?" }
    ]);
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        if (isOpen) {
            scrollToBottom();
        }
    }, [messages, isOpen]);

    const handleSend = async () => {
        if (!message.trim() || loading) return;

        const userMessage = message.trim();
        setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
        setMessage("");
        setLoading(true);

        try {
            const res = await fetch(`${API_BASE}/chatbot/query`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ message: userMessage }),
            });

            if (!res.body) throw new Error("No response body");

            // Add an empty assistant message to start filling
            setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let done = false;

            while (!done) {
                const { value, done: doneReading } = await reader.read();
                done = doneReading;
                const chunkValue = decoder.decode(value, { stream: !done });

                setMessages((prev) => {
                    const newMessages = [...prev];
                    const lastIndex = newMessages.length - 1;
                    const lastMessage = newMessages[lastIndex];

                    if (lastMessage.role === "assistant") {
                        newMessages[lastIndex] = {
                            ...lastMessage,
                            content: lastMessage.content + chunkValue
                        };
                    }
                    return newMessages;
                });
            }

        } catch (error) {
            console.error(error);
            setMessages((prev) => [...prev, { role: "assistant", content: "Une erreur est survenue lors de la communication avec le serveur." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            {/* FAB Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`fixed bottom-24 lg:bottom-8 right-6 h-16 w-16 rounded-full shadow-2xl transition-all duration-500 flex items-center justify-center z-50 group ${isOpen
                    ? "bg-brand-primary rotate-180"
                    : "bg-brand-secondary hover:scale-110 active:scale-95"
                    }`}
            >
                <div className="absolute inset-0 rounded-full bg-brand-secondary opacity-20 animate-ping group-hover:opacity-0 transition-opacity" />
                {isOpen ? (
                    <svg className="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                ) : (
                    <svg className="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                )}
            </button>

            {/* Chat Window */}
            {isOpen && (
                <div className="fixed bottom-44 lg:bottom-28 right-6 w-[400px] max-w-[calc(100vw-3rem)] h-[600px] max-h-[70vh] rounded-[24px] shadow-2xl bg-white border border-slate-200/50 flex flex-col overflow-hidden z-50 animate-slide-up glass-panel">
                    {/* Header */}
                    <div className="bg-brand-primary p-6 relative overflow-hidden">
                        {/* Decorative Background Element */}
                        <div className="absolute -top-10 -right-10 w-32 h-32 bg-brand-secondary rounded-full opacity-10 blur-3xl" />

                        <div className="flex items-center gap-4 relative z-10">
                            <div className="h-12 w-12 rounded-xl bg-brand-secondary flex items-center justify-center shadow-lg shadow-brand-secondary/20 border border-white/10">
                                <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                            </div>
                            <div>
                                <h3 className="font-bold text-white text-lg tracking-tight">PURE AI Assistant</h3>
                                <div className="flex items-center gap-1.5 line-clamp-1">
                                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                                    <p className="text-xs text-slate-400 font-medium">Logistique & Suivi en temps réel</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50">
                        {messages.map((msg, i) => (
                            <div key={i} className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"} animate-fade-in`}>
                                <div
                                    className={`max-w-[85%] px-5 py-3 rounded-2xl text-sm leading-relaxed ${msg.role === "user"
                                        ? "bg-brand-secondary text-white shadow-lg shadow-brand-secondary/10 rounded-tr-none"
                                        : "bg-white border border-slate-200 text-slate-700 shadow-sm rounded-tl-none"
                                        }`}
                                >
                                    {msg.content}
                                </div>
                                <span className="text-[10px] text-slate-400 mt-1.5 px-1 uppercase tracking-wider font-semibold">
                                    {msg.role === "user" ? "Vous" : "Pure AI"}
                                </span>
                            </div>
                        ))}
                        {loading && (
                            <div className="flex flex-col items-start animate-fade-in">
                                <div className="bg-white border border-slate-200 px-5 py-4 rounded-2xl rounded-tl-none shadow-sm">
                                    <div className="flex gap-1.5">
                                        <span className="w-1.5 h-1.5 bg-brand-secondary rounded-full animate-bounce [animation-delay:-0.3s]" />
                                        <span className="w-1.5 h-1.5 bg-brand-secondary rounded-full animate-bounce [animation-delay:-0.15s]" />
                                        <span className="w-1.5 h-1.5 bg-brand-secondary rounded-full animate-bounce" />
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="p-6 border-t border-slate-100 bg-white">
                        <div className="relative group">
                            <input
                                type="text"
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                                placeholder="Numéro d'expédition ou question..."
                                className="w-full pl-5 pr-14 py-3.5 rounded-2xl border border-slate-200 bg-slate-50 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-secondary/10 focus:border-brand-secondary/50 focus:bg-white transition-all duration-300"
                            />
                            <button
                                onClick={handleSend}
                                disabled={loading || !message.trim()}
                                className="absolute right-2 top-2 bottom-2 px-3 rounded-xl bg-brand-primary text-white hover:bg-brand-secondary disabled:opacity-30 disabled:hover:bg-brand-primary transition-all duration-300 flex items-center justify-center"
                            >
                                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 12l6 6L20 6" />
                                </svg>
                            </button>
                        </div>
                        <p className="text-[10px] text-center text-slate-400 mt-4 uppercase tracking-widest font-bold">
                            Powered by PURE TRADE Logistics Intelligence
                        </p>
                    </div>
                </div>
            )}
        </>
    );
}

