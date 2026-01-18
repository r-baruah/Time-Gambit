"use client";

import { useState, useEffect } from "react";
import { Settings, X, Check, AlertCircle } from "lucide-react";

type SettingsData = {
    openrouter_api_key: string;
    openrouter_model: string;
    openai_api_key: string;
    google_client_id: string;
    google_client_secret: string;
    working_hours_start: string;
    working_hours_end: string;
    lunch_start: string;
    lunch_end: string;
};

const DEFAULT_MODELS = [
    { id: "z-ai/glm-4.5-air:free", name: "GLM 4.5 Air (Free)" },
    { id: "openai/gpt-4o-mini", name: "GPT-4o Mini" },
    { id: "openai/gpt-4o", name: "GPT-4o" },
    { id: "anthropic/claude-3-haiku", name: "Claude 3 Haiku" },
    { id: "anthropic/claude-3-sonnet", name: "Claude 3 Sonnet" },
    { id: "google/gemini-flash-1.5", name: "Gemini Flash 1.5" },
];

export default function SettingsModal({
    isOpen,
    onClose,
}: {
    isOpen: boolean;
    onClose: () => void;
}) {
    const [settings, setSettings] = useState<SettingsData>({
        openrouter_api_key: "",
        openrouter_model: "z-ai/glm-4.5-air:free",
        openai_api_key: "",
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
                    setSettings(data);
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
            const res = await fetch("http://localhost:8000/settings/test", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ api_key: settings.openrouter_api_key, model: settings.openrouter_model }),
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
            <div className="bg-card border border-border rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="p-4 border-b border-border flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Settings className="w-5 h-5" />
                        <h2 className="font-semibold text-lg">Settings</h2>
                    </div>
                    <button onClick={onClose} className="p-1 hover:bg-muted rounded-lg transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-6">
                    {/* AI Provider Settings */}
                    <section>
                        <h3 className="font-medium mb-3 text-sm text-muted-foreground uppercase tracking-wide">AI Provider</h3>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">OpenRouter API Key</label>
                                <input
                                    type="password"
                                    value={settings.openrouter_api_key}
                                    onChange={(e) => setSettings({ ...settings, openrouter_api_key: e.target.value })}
                                    placeholder="sk-or-..."
                                    className="w-full bg-muted/50 border border-border rounded-lg px-3 py-2 text-sm"
                                />
                                <p className="text-xs text-muted-foreground mt-1">
                                    Get your key from <a href="https://openrouter.ai/settings/keys" target="_blank" className="text-primary hover:underline">openrouter.ai</a>
                                </p>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Model</label>
                                <select
                                    value={settings.openrouter_model}
                                    onChange={(e) => setSettings({ ...settings, openrouter_model: e.target.value })}
                                    className="w-full bg-muted/50 border border-border rounded-lg px-3 py-2 text-sm"
                                >
                                    {DEFAULT_MODELS.map((model) => (
                                        <option key={model.id} value={model.id}>
                                            {model.name}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <button
                                onClick={testConnection}
                                disabled={testStatus === "testing"}
                                className="bg-secondary text-secondary-foreground px-4 py-2 rounded-lg text-sm hover:bg-secondary/80 transition-colors disabled:opacity-50"
                            >
                                {testStatus === "testing" ? "Testing..." : "Test Connection"}
                            </button>

                            {testMessage && (
                                <div className={`text-sm p-2 rounded-lg ${testStatus === "success" ? "bg-green-500/10 text-green-400" :
                                        testStatus === "error" ? "bg-red-500/10 text-red-400" :
                                            "bg-muted text-muted-foreground"
                                    }`}>
                                    {testMessage}
                                </div>
                            )}
                        </div>
                    </section>

                    {/* Working Hours */}
                    <section>
                        <h3 className="font-medium mb-3 text-sm text-muted-foreground uppercase tracking-wide">Working Hours</h3>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">Start Time</label>
                                <input
                                    type="time"
                                    value={settings.working_hours_start}
                                    onChange={(e) => setSettings({ ...settings, working_hours_start: e.target.value })}
                                    className="w-full bg-muted/50 border border-border rounded-lg px-3 py-2 text-sm"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">End Time</label>
                                <input
                                    type="time"
                                    value={settings.working_hours_end}
                                    onChange={(e) => setSettings({ ...settings, working_hours_end: e.target.value })}
                                    className="w-full bg-muted/50 border border-border rounded-lg px-3 py-2 text-sm"
                                />
                            </div>
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
                    </section>
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-border flex justify-end gap-2">
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
                            Save Settings
                        </>}
                    </button>
                </div>
            </div>
        </div>
    );
}
