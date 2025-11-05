"use client";

import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Eye, EyeOff, Key, AlertTriangle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ProviderLabel } from "@/components/providers/ProviderLabel";

const STORAGE_KEY = "ragrace_parse_api_keys";

interface ApiKeys {
  llamaindex?: string;
  reducto?: string;
  landingai?: string;
}

interface ApiKeyFormProps {
  onKeysChange: (keys: ApiKeys, hasAtLeastOne: boolean) => void;
  disabled?: boolean;
}

export function ApiKeyForm({ onKeysChange, disabled = false }: ApiKeyFormProps) {
  const [keys, setKeys] = useState<ApiKeys>({});
  const [showKeys, setShowKeys] = useState({
    llamaindex: false,
    reducto: false,
    landingai: false,
  });

  // Load keys from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as ApiKeys;
        setKeys(parsed);
        // Notify parent of loaded keys
        const hasAtLeastOne = Object.values(parsed).some(
          (value) => typeof value === "string" && value.trim().length > 0
        );
        onKeysChange(parsed, hasAtLeastOne);
      }
    } catch (error) {
      console.error("Failed to load API keys from localStorage:", error);
    }
  }, []);

  // Save to localStorage whenever keys change
  const handleKeyChange = (provider: keyof ApiKeys, value: string) => {
    const newKeys = { ...keys, [provider]: value };
    setKeys(newKeys);

    // Save to localStorage
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newKeys));
    } catch (error) {
      console.error("Failed to save API keys to localStorage:", error);
    }

    // Notify parent
    const hasAtLeastOne = Object.values(newKeys).some(
      (value) => typeof value === "string" && value.trim().length > 0
    );
    onKeysChange(newKeys, hasAtLeastOne);
  };

  const toggleShowKey = (provider: keyof typeof showKeys) => {
    setShowKeys({ ...showKeys, [provider]: !showKeys[provider] });
  };

  const clearAllKeys = () => {
    setKeys({});
    localStorage.removeItem(STORAGE_KEY);
    onKeysChange({}, false);
  };

  const hasAnyKey = Object.values(keys).some((v) => v && v.trim());

  return (
    <div className="border rounded-lg p-6 bg-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Key className="h-5 w-5 text-gray-500" />
          <h2 className="text-lg font-semibold">API Keys</h2>
        </div>
        {hasAnyKey && (
          <Button variant="ghost" size="sm" onClick={clearAllKeys}>
            Clear All
          </Button>
        )}
      </div>

      <Alert className="mb-4">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Your API keys are stored in your browser&apos;s localStorage and sent directly to
          the parsing providers. They are never stored on our servers.
        </AlertDescription>
      </Alert>

      <div className="space-y-4">
        {/* LlamaIndex Key */}
        <div className="space-y-2">
          <Label
            htmlFor="llamaindex-key"
            className="flex items-center justify-between gap-2"
          >
            <ProviderLabel
              provider="llamaindex"
              size={20}
              className="gap-2"
              nameClassName="text-sm font-medium"
            />
            <span className="text-xs text-gray-500">(optional)</span>
          </Label>
          <div className="relative">
            <Input
              id="llamaindex-key"
              type={showKeys.llamaindex ? "text" : "password"}
              placeholder="llx_..."
              value={keys.llamaindex || ""}
              onChange={(e) => handleKeyChange("llamaindex", e.target.value)}
              disabled={disabled}
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => toggleShowKey("llamaindex")}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
            >
              {showKeys.llamaindex ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>

        {/* Reducto Key */}
        <div className="space-y-2">
          <Label
            htmlFor="reducto-key"
            className="flex items-center justify-between gap-2"
          >
            <ProviderLabel
              provider="reducto"
              size={20}
              className="gap-2"
              nameClassName="text-sm font-medium"
            />
            <span className="text-xs text-gray-500">(optional)</span>
          </Label>
          <div className="relative">
            <Input
              id="reducto-key"
              type={showKeys.reducto ? "text" : "password"}
              placeholder="sk_..."
              value={keys.reducto || ""}
              onChange={(e) => handleKeyChange("reducto", e.target.value)}
              disabled={disabled}
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => toggleShowKey("reducto")}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
            >
              {showKeys.reducto ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>

        {/* LandingAI Key */}
        <div className="space-y-2">
          <Label
            htmlFor="landingai-key"
            className="flex items-center justify-between gap-2"
          >
            <ProviderLabel
              provider="landingai"
              size={20}
              className="gap-2"
              nameClassName="text-sm font-medium"
            />
            <span className="text-xs text-gray-500">(optional)</span>
          </Label>
          <div className="relative">
            <Input
              id="landingai-key"
              type={showKeys.landingai ? "text" : "password"}
              placeholder="land_..."
              value={keys.landingai || ""}
              onChange={(e) => handleKeyChange("landingai", e.target.value)}
              disabled={disabled}
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => toggleShowKey("landingai")}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
            >
              {showKeys.landingai ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>
      </div>

      <p className="text-sm text-gray-500 mt-4">
        Provide at least one API key to enable PDF parsing. Only providers with keys will be run.
      </p>
    </div>
  );
}
