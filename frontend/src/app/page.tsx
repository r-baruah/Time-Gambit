"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Calendar as CalendarIcon, Terminal, Clock, Settings } from "lucide-react";
import { cn } from "@/lib/utils";
import SettingsModal from "@/components/SettingsModal";

// Types
type Message = {
    role: "user" | "assistant";
    content: string;
};

type Log = {
    id: number;
    message: string;
    timestamp: string;
};

export default function Home() {
    const [messages, setMessages] = useState<Message[]>([
        { role: "assistant", content: "Hello! I'm your Agentic Scheduler. I can check your calendar and help plan your day. What would you like to do?" }
    ]);
    const [input, setInput] = useState("");
    const [logs, setLogs] = useState<Log[]>([
        { id: 1, message: "System initialized.", timestamp: "" },
        { id: 2, message: "Router Agent ready.", timestamp: "" }
    ]);
    const [loading, setLoading] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [authLoading, setAuthLoading] = useState(true);
    const [settingsOpen, setSettingsOpen] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Check auth status on mount and handle callback
    useEffect(() => {
        // Check if returning from OAuth callback
        const urlParams = new URLSearchParams(window.location.search);
        const authStatus = urlParams.get('auth');
        if (authStatus === 'success') {
            setIsAuthenticated(true);
            setLogs(prev => [...prev, { id: Date.now(), message: "Google Calendar connected successfully!", timestamp: new Date().toLocaleTimeString() }]);
            // Clean URL
            window.history.replaceState({}, document.title, window.location.pathname);
        } else if (authStatus === 'failed') {
            setLogs(prev => [...prev, { id: Date.now(), message: "Error: Failed to connect Google Calendar.", timestamp: new Date().toLocaleTimeString() }]);
            window.history.replaceState({}, document.title, window.location.pathname);
        }

        // Check current auth status from backend
        const checkAuth = async () => {
            try {
                const res = await fetch("http://localhost:8000/auth/status");
                const data = await res.json();
                setIsAuthenticated(data.authenticated);
            } catch (err) {
                console.error("Failed to check auth status");
            } finally {
                setAuthLoading(false);
            }
        };
        checkAuth();
    }, []);

    // Hydration fix: Populate initial timestamps on client side
    useEffect(() => {
        setLogs(prev => prev.map(log =>
            log.timestamp === "" ? { ...log, timestamp: new Date().toLocaleTimeString() } : log
        ));
    }, []);

    // Auto-scroll chat
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleLogin = async () => {
        try {
            const res = await fetch("http://localhost:8000/auth/login");
            const data = await res.json();
            // Redirect user to Google
            window.location.href = data.auth_url;
        } catch (err) {
            setLogs(prev => [...prev, { id: Date.now(), message: "Error: Could not initiate login.", timestamp: new Date().toLocaleTimeString() }]);
        }
    };

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMsg = input;
        setInput("");
        setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
        setLoading(true);

        try {
            // Phase 1: Mock Backend Call
            const res = await fetch("http://localhost:8000/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMsg }),
            });

            if (!res.ok) throw new Error("Failed to connect to backend");

            const data = await res.json();

            // Update UI with backend response
            // Backend now returns FULL history, so we replace state
            const newMessages = data.messages; // Backend sends correctly formatted objects
            const newLogs = data.reasoning_logs.map((log: string, i: number) => ({
                id: Date.now() + i,
                message: log,
                timestamp: new Date().toLocaleTimeString()
            }));

            setMessages(newMessages); // Replace, don't append
            setLogs(newLogs);         // Replace, don't append

        } catch (err) {
            setMessages((prev) => [...prev, { role: "assistant", content: "Error: Could not reach the Agent backend. Make sure it's running on port 8000." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <SettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />

            <main className="flex h-full flex-col p-4 gap-4">
                {/* Top Row: Chat & Calendar */}
                <div className="flex flex-1 gap-4 min-h-0">

                    {/* LEFT: Chat Interface */}
                    <div className="w-1/3 flex flex-col rounded-xl border border-border bg-card/50 backdrop-blur-sm overflow-hidden shadow-sm">
                        <div className="p-4 border-b border-border bg-muted/20 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse" />
                                <h2 className="font-semibold tracking-tight">Agent Interface</h2>
                            </div>
                            <button
                                onClick={() => setSettingsOpen(true)}
                                className="p-1.5 hover:bg-muted rounded-lg transition-colors text-muted-foreground hover:text-foreground"
                                title="Settings"
                            >
                                <Settings className="w-4 h-4" />
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={scrollRef}>
                            {messages.map((msg, i) => (
                                <div key={i} className={cn(
                                    "flex flex-col max-w-[85%] rounded-2xl px-4 py-2.5 text-sm",
                                    msg.role === "user"
                                        ? "self-end bg-primary text-primary-foreground rounded-br-none"
                                        : "self-start bg-muted text-foreground rounded-bl-none"
                                )}>
                                    <span>{msg.content}</span>
                                </div>
                            ))}
                            {loading && (
                                <div className="self-start bg-muted/50 rounded-2xl px-4 py-2 text-xs text-muted-foreground animate-pulse">
                                    Agent is thinking...
                                </div>
                            )}
                        </div>

                        <div className="p-4 border-t border-border bg-background/50">
                            <div className="flex gap-2">
                                <input
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={(e) => e.key === "Enter" && handleSend()}
                                    placeholder="Ask to schedule something..."
                                    className="flex-1 bg-muted/50 border-transparent focus:border-primary rounded-lg px-4 py-2 text-sm outline-none transition-all placeholder:text-muted-foreground/70"
                                />
                                <button
                                    onClick={handleSend}
                                    disabled={loading}
                                    className="bg-primary text-primary-foreground p-2 rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
                                >
                                    <Send className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* RIGHT: Calendar View */}
                    <div className="flex-1 flex flex-col rounded-xl border border-border bg-card overflow-hidden shadow-sm relative group">
                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-10">
                            <CalendarIcon className="w-32 h-32" />
                        </div>
                        <div className="p-4 border-b border-border bg-muted/20 flex justify-between items-center">
                            <div className="flex items-center gap-2">
                                <CalendarIcon className="w-4 h-4 text-muted-foreground" />
                                <h2 className="font-semibold tracking-tight">Google Calendar</h2>
                            </div>
                            {authLoading ? (
                                <div className="text-xs text-muted-foreground">Checking...</div>
                            ) : isAuthenticated ? (
                                <div className="text-xs text-green-400 flex items-center gap-1">
                                    <div className="w-2 h-2 rounded-full bg-green-500" />
                                    Connected
                                </div>
                            ) : (
                                <button
                                    onClick={handleLogin}
                                    className="text-xs bg-primary text-primary-foreground px-3 py-1 rounded-md hover:bg-primary/90 transition-colors"
                                >
                                    Connect Google Calendar
                                </button>
                            )}
                        </div>

                        <div className="flex-1 bg-white/5 p-0 relative">
                            {/* Iframe Placeholder - In Phase 3, we will verify the user email URL */}
                            <iframe
                                src="https://calendar.google.com/calendar/embed?src=en.usa%23holiday%40group.v.calendar.google.com&ctz=America%2FNew_York"
                                style={{ border: 0 }}
                                width="100%"
                                height="100%"
                                frameBorder="0"
                                scrolling="no"
                                className="w-full h-full opacity-80 hover:opacity-100 transition-opacity"
                            ></iframe>
                        </div>
                    </div>

                </div>

                {/* Bottom Row: Reasoning Logs */}
                <div className="h-48 flex flex-col rounded-xl border border-border bg-[#0a0a0a] overflow-hidden shadow-sm font-mono text-xs">
                    <div className="px-4 py-2 border-b border-border bg-muted/10 flex items-center justify-between">
                        <div className="flex items-center gap-2 text-muted-foreground">
                            <Terminal className="w-3.5 h-3.5" />
                            <span className="font-medium">System Reasoning Logs</span>
                        </div>
                        <div className="flex items-center gap-2 text-muted-foreground/50">
                            <Clock className="w-3 h-3" />
                            <span>Real-time</span>
                        </div>
                    </div>
                    <div className="flex-1 p-3 overflow-y-auto space-y-1 logs-scrollbar">
                        {logs.map((log) => (
                            <div key={log.id} className="flex gap-3 font-mono">
                                <span className="text-muted-foreground shrink-0">[{log.timestamp}]</span>
                                <span className={cn(
                                    "break-all",
                                    log.message.includes("Error") ? "text-red-400" :
                                        log.message.includes("Router") ? "text-blue-400" :
                                            log.message.includes("Calendar") ? "text-yellow-400" :
                                                "text-green-400"
                                )}>
                                    {log.message}
                                </span>
                            </div>
                        ))}
                        <div className="animate-pulse text-muted-foreground/30">_</div>
                    </div>
                </div>
            </main>
        </>
    );
}
