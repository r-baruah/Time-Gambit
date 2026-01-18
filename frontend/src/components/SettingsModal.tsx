"use client";

import { useState, useEffect } from "react";
import { Settings, X, Check, AlertCircle } from "lucide-react";

type SettingsData = {
    llm_provider: string;
    openrouter_api_key: string;
    openrouter_model: string;
    openai_api_key: string;
    openai_model: string;
    google_api_key: string;
    google_model: string;
    google_client_id: string;
    google_client_secret: string;
    working_hours_start: string;
    working_hours_end: string;
    lunch_start: string;
    lunch_end: string;
};

const PROVIDERS = [
    { id: "google", name: "Google Gemini (Default)" },
    { id: "openrouter", name: "OpenRouter (Fallback)" },
    { id: "openai", name: "OpenAI" },
];

const MODELS = {
    openrouter: [
        { id: "z-ai/glm-4.5-air:free", name: "GLM 4.5 Air (Free)" },
        { id: "openai/gpt-4o-mini", name: "GPT-4o Mini" },
        { id: "anthropic/claude-3-sonnet", name: "Claude 3 Sonnet" },
    ],
    openai: [
        { id: "gpt-4o", name: "GPT-4o" },
        { id: "gpt-4o-mini", name: "GPT-4o Mini" },
        { id: "gpt-3.5-turbo", name: "GPT-3.5 Turbo" },
    ],
    google: [
        { id: "gemini-2.5-flash", name: "Gemini 2.5 Flash (Default)" },
        { id: "gemini-2.5-pro", name: "Gemini 2.5 Pro" },
        { id: "gemini-2.0-flash-thinking-exp-01-21", name: "Gemini 2.0 Flash Thinking (Exp)" },
    ]
};

export default function SettingsModal({
    isOpen,
    onClose,
}: {
    isOpen: boolean;
    onClose: () => void;
}) {
    const [settings, setSettings] = useState<SettingsData>({
        llm_provider: "google",
        openrouter_api_key: "",
        openrouter_model: "z-ai/glm-4.5-air:free",
        openai_api_key: "",
        openai_model: "gpt-4o",
        google_api_key: "",
        google_model: "gemini-2.5-flash",
        google_client_id: "",
        google_client_secret: "",
        working_hours_start: "09:00",
        working_hours_end: "17:00",
        lunch_start: "13:00",
        lunch_end: "14:00",
    });
    const [testStatus, setTestStatus] = useState<"idle" | "testing" | "success" | "error">("idle");
    const [testMessage, setTestMessage] = useState("");
    const [saving, setSaving] = useState(false);

    // Load settings on mount
    useEffect(() => {
        const loadSettings = async () => {
            try {
                const res = await fetch("http://localhost:8000/settings");
                if (res.ok) {
                    const data = await res.json();
                    setSettings(prev => ({ ...prev, ...data }));
                }
            } catch (err) {
                console.error("Failed to load settings");
            }
        };
        if (isOpen) loadSettings();
    }, [isOpen]);

    const handleSave = async () => {
        setSaving(true);
        try {
            const res = await fetch("http://localhost:8000/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(settings),
            });
            if (res.ok) {
                onClose();
            }
        } catch (err) {
            console.error("Failed to save settings");
        } finally {
            setSaving(false);
        }
    };

    const testConnection = async () => {
        setTestStatus("testing");
        setTestMessage("Testing API connection...");
        try {
            let apiKey = "";
            let model = "";
            const provider = settings.llm_provider;

            if (provider === "openrouter") {
                apiKey = settings.openrouter_api_key;
                model = settings.openrouter_model;
            } else if (provider === "openai") {
                apiKey = settings.openai_api_key;
                model = settings.openai_model;
            } else if (provider === "google") {
                apiKey = settings.google_api_key;
                model = settings.google_model;
            }

            const res = await fetch("http://localhost:8000/settings/test", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    provider,
                    api_key: apiKey,
                    model: model
                }),
            });
            const data = await res.json();
            if (data.success) {
                setTestStatus("success");
                setTestMessage(`✓ Connected! Response time: ${data.latency}ms`);
            } else {
                setTestStatus("error");
                setTestMessage(`✗ Error: ${data.error}`);
            }
        } catch (err) {
            setTestStatus("error");
            setTestMessage("✗ Failed to connect to backend");
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-card border border-border rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
                {/* Header */}
                <div className="p-4 border-b border-border flex items-center justify-between bg-muted/20">
                    <div className="flex items-center gap-2">
                        <Settings className="w-5 h-5 text-primary" />
                        <h2 className="font-semibold text-lg">Agent Configuration</h2>
                    </div>
                    <button onClick={onClose} className="p-1 hover:bg-muted rounded-lg transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-8">
                    {/* AI Provider Section */}
                    <section className="space-y-4">
                        <div className="flex items-center justify-between">
                            <h3 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">AI Provider</h3>
                            <select
                                value={settings.llm_provider}
                                onChange={(e) => setSettings({ ...settings, llm_provider: e.target.value })}
                                className="bg-muted border border-border rounded-md px-2 py-1 text-sm font-medium"
                            >
                                {PROVIDERS.map(p => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                ))}
                            </select>
                        </div>

                        <div className="bg-muted/30 border border-border rounded-lg p-4 space-y-4">
                            {/* OpenRouter Inputs */}
                            {settings.llm_provider === "openrouter" && (
                                <>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">OpenRouter Key</label>
                                        <input
                                            type="password"
                                            value={settings.openrouter_api_key}
                                            onChange={(e) => setSettings({ ...settings, openrouter_api_key: e.target.value })}
                                            placeholder="sk-or-..."
                                            className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm"
                                        />
                                        <p className="text-xs text-muted-foreground mt-1">
                                            Allows access to free models. Get key from <a href="https://openrouter.ai/keys" className="text-primary hover:underline">openrouter.ai</a>
                                        </p>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Model</label>
                                        <select
                                            value={settings.openrouter_model}
                                            onChange={(e) => setSettings({ ...settings, openrouter_model: e.target.value })}
                                            className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm"
                                        >
                                            {MODELS.openrouter.map((m) => (
                                                <option key={m.id} value={m.id}>{m.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                </>
                            )}

                            {/* OpenAI Inputs */}
                            {settings.llm_provider === "openai" && (
                                <>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">OpenAI API Key</label>
                                        <input
                                            type="password"
                                            value={settings.openai_api_key}
                                            onChange={(e) => setSettings({ ...settings, openai_api_key: e.target.value })}
                                            placeholder="sk-..."
                                            className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Model</label>
                                        <select
                                            value={settings.openai_model}
                                            onChange={(e) => setSettings({ ...settings, openai_model: e.target.value })}
                                            className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm"
                                        >
                                            {MODELS.openai.map((m) => (
                                                <option key={m.id} value={m.id}>{m.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                </>
                            )}

                            {/* Google Inputs */}
                            {settings.llm_provider === "google" && (
                                <>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Google API Key</label>
                                        <input
                                            type="password"
                                            value={settings.google_api_key}
                                            onChange={(e) => setSettings({ ...settings, google_api_key: e.target.value })}
                                            placeholder="AIza..."
                                            className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm"
                                        />
                                        <p className="text-xs text-muted-foreground mt-1">
                                            Leave empty/masked to use our default API (subject to rate limits).
                                            <br />
                                            For best performance, <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">get your own free key here</a>.
                                        </p>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Model</label>
                                        <select
                                            value={settings.google_model}
                                            onChange={(e) => setSettings({ ...settings, google_model: e.target.value })}
                                            className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm"
                                        >
                                            {MODELS.google.map((m) => (
                                                <option key={m.id} value={m.id}>{m.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                </>
                            )}

                            <div className="pt-2">
                                <button
                                    onClick={testConnection}
                                    disabled={testStatus === "testing"}
                                    className="text-xs bg-secondary hover:bg-secondary/80 text-secondary-foreground px-3 py-1.5 rounded-md transition-colors"
                                >
                                    {testStatus === "testing" ? "Testing..." : "Test Connection"}
                                </button>
                                {testMessage && (
                                    <span className={`ml-3 text-xs ${testStatus === "success" ? "text-green-500" : "text-red-500"}`}>
                                        {testMessage}
                                    </span>
                                )}
                            </div>
                        </div>
                    </section>

                    {/* Working Hours */}
                    <section>
                        <h3 className="font-medium mb-3 text-sm text-muted-foreground uppercase tracking-wide">Constraints</h3>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">Day Start</label>
                                <input
                                    type="time"
                                    value={settings.working_hours_start}
                                    onChange={(e) => setSettings({ ...settings, working_hours_start: e.target.value })}
                                    className="w-full bg-muted/50 border border-border rounded-lg px-3 py-2 text-sm"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">Day End</label>
                                <input
                                    type="time"
                                    value={settings.working_hours_end}
                                    onChange={(e) => setSettings({ ...settings, working_hours_end: e.target.value })}
                                    className="w-full bg-muted/50 border border-border rounded-lg px-3 py-2 text-sm"
                                />
                            </div>
                            <div className="col-span-2 grid grid-cols-2 gap-4 border-t border-border pt-4 mt-2">
                                <div>
                                    <label className="block text-sm font-medium mb-1">Lunch Start</label>
                                    <input
                                        type="time"
                                        value={settings.lunch_start}
                                        onChange={(e) => setSettings({ ...settings, lunch_start: e.target.value })}
                                        className="w-full bg-muted/50 border border-border rounded-lg px-3 py-2 text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1">Lunch End</label>
                                    <input
                                        type="time"
                                        value={settings.lunch_end}
                                        onChange={(e) => setSettings({ ...settings, lunch_end: e.target.value })}
                                        className="w-full bg-muted/50 border border-border rounded-lg px-3 py-2 text-sm"
                                    />
                                </div>
                            </div>
                        </div>
                    </section>
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-border flex justify-end gap-2 bg-muted/20">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm rounded-lg hover:bg-muted transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="bg-primary text-primary-foreground px-4 py-2 rounded-lg text-sm hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-2"
                    >
                        {saving ? "Saving..." : <>
                            <Check className="w-4 h-4" />
                            Save Configuration
                        </>}
                    </button>
                </div>
            </div>
        </div>
    );
}
