"use client";

import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Eye, EyeOff, Key, AlertTriangle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ProviderLabel } from "@/components/providers/ProviderLabel";

const STORAGE_KEY = "ragrace_parse_api_keys";
const CONFIG_STORAGE_KEY = "ragrace_parse_configs";

interface ApiKeys {
  llamaindex?: string;
  reducto?: string;
  landingai?: string;
}

interface ProviderConfigs {
  llamaindex?: {
    parse_mode: string;
    model: string;
  };
  reducto?: {
    mode: string;
    summarize_figures: boolean;
  };
  landingai?: {
    model: string;
  };
}

interface ApiKeyFormProps {
  onKeysChange: (keys: ApiKeys, hasAtLeastOne: boolean) => void;
  onConfigsChange?: (configs: ProviderConfigs) => void;
  disabled?: boolean;
}

// Pricing information (from backend config)
const PRICING = {
  llamaindex: {
    usd_per_credit: 0.001,
    models: [
      {
        parse_mode: "parse_page_with_llm",
        model: "default",
        credits_per_page: 3,
        description: "Cost-effective",
        detailedDescription: "Cost-effective - 3 credits/page ($0.003/page)",
      },
      {
        parse_mode: "parse_page_with_agent",
        model: "openai-gpt-4-1-mini",
        credits_per_page: 20,
        description: "Agentic",
        detailedDescription: "Agentic - 20 credits/page ($0.020/page)",
      },
      {
        parse_mode: "parse_page_with_agent",
        model: "anthropic-sonnet-4.0",
        credits_per_page: 90,
        description: "Agentic Plus",
        detailedDescription: "Agentic Plus - 90 credits/page ($0.090/page)",
      },
    ],
  },
  reducto: {
    usd_per_credit: 0.015,
    models: [
      {
        mode: "standard",
        summarize_figures: false,
        credits_per_page: 1,
        description: "Standard Page",
        detailedDescription: "Standard Page - 1 credit/page ($0.015/page)",
      },
      {
        mode: "complex",
        summarize_figures: true,
        credits_per_page: 2,
        description: "Complex Page (VLM enhance)",
        detailedDescription: "Complex Page (VLM enhance) - 2 credits/page ($0.030/page)",
      },
    ],
  },
  landingai: {
    usd_per_credit: 0.01,
    models: [
      {
        model: "dpt-2",
        credits_per_page: 3,
        description: "DPT-2",
        detailedDescription: "DPT-2 - 3 credits/page ($0.030/page)",
      },
    ],
  },
};

export function ApiKeyForm({
  onKeysChange,
  onConfigsChange,
  disabled = false,
}: ApiKeyFormProps) {
  const [keys, setKeys] = useState<ApiKeys>({});
  const [configs, setConfigs] = useState<ProviderConfigs>({
    llamaindex: {
      parse_mode: "parse_page_with_agent",
      model: "openai-gpt-4-1-mini",
    },
    reducto: {
      mode: "standard",
      summarize_figures: false,
    },
    landingai: {
      model: "dpt-2",
    },
  });
  const [showKeys, setShowKeys] = useState({
    llamaindex: false,
    reducto: false,
    landingai: false,
  });

  // Load keys and configs from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as ApiKeys;
        setKeys(parsed);
        const hasAtLeastOne = Object.values(parsed).some(
          (value) => typeof value === "string" && value.trim().length > 0
        );
        onKeysChange(parsed, hasAtLeastOne);
      }

      const storedConfigs = localStorage.getItem(CONFIG_STORAGE_KEY);
      if (storedConfigs) {
        const parsedConfigs = JSON.parse(storedConfigs) as ProviderConfigs;
        setConfigs(parsedConfigs);
        onConfigsChange?.(parsedConfigs);
      } else {
        // Save default configs
        localStorage.setItem(CONFIG_STORAGE_KEY, JSON.stringify(configs));
        onConfigsChange?.(configs);
      }
    } catch (error) {
      console.error("Failed to load from localStorage:", error);
    }
  }, []);

  // Save to localStorage whenever keys change
  const handleKeyChange = (provider: keyof ApiKeys, value: string) => {
    const newKeys = { ...keys, [provider]: value };
    setKeys(newKeys);

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newKeys));
    } catch (error) {
      console.error("Failed to save API keys to localStorage:", error);
    }

    const hasAtLeastOne = Object.values(newKeys).some(
      (value) => typeof value === "string" && value.trim().length > 0
    );
    onKeysChange(newKeys, hasAtLeastOne);
  };

  const handleConfigChange = (
    provider: keyof ProviderConfigs,
    configKey: string,
    value: any
  ) => {
    const newConfigs = {
      ...configs,
      [provider]: {
        ...configs[provider],
        [configKey]: value,
      },
    };
    setConfigs(newConfigs);

    try {
      localStorage.setItem(CONFIG_STORAGE_KEY, JSON.stringify(newConfigs));
    } catch (error) {
      console.error("Failed to save configs to localStorage:", error);
    }

    onConfigsChange?.(newConfigs);
  };

  // Update multiple config fields at once to avoid race conditions
  const handleFullConfigChange = (
    provider: keyof ProviderConfigs,
    updates: Record<string, any>
  ) => {
    const newConfigs = {
      ...configs,
      [provider]: {
        ...configs[provider],
        ...updates,
      },
    };
    setConfigs(newConfigs);

    try {
      localStorage.setItem(CONFIG_STORAGE_KEY, JSON.stringify(newConfigs));
    } catch (error) {
      console.error("Failed to save configs to localStorage:", error);
    }

    onConfigsChange?.(newConfigs);
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
          <h2 className="text-lg font-semibold">Configuration</h2>
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
          Your API keys are stored in your browser&apos;s localStorage and sent
          directly to the parsing providers. They are never stored on our
          servers.
        </AlertDescription>
      </Alert>

      <div className="space-y-4">
        {/* LlamaIndex */}
        <div className="pb-4 border-b">
          <div className="flex items-center mb-3 gap-2">
            <ProviderLabel
              provider="llamaindex"
              size={20}
              className="gap-2"
              nameClassName="text-sm font-medium"
            />
            <span className="text-xs text-gray-500">(optional)</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Left: API Key */}
            <div>
              <Label htmlFor="llamaindex-key" className="text-xs text-gray-600 mb-2 block">
                API Key
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
            {/* Right: Model */}
            <div>
              <Label htmlFor="llamaindex-model" className="text-xs text-gray-600 mb-2 block">
                Model
              </Label>
              <Select
                value={`${configs.llamaindex?.parse_mode}:${configs.llamaindex?.model}`}
                onValueChange={(value) => {
                  const [parse_mode, model] = value.split(":");
                  handleFullConfigChange("llamaindex", { parse_mode, model });
                }}
                disabled={disabled}
              >
                <SelectTrigger id="llamaindex-model">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PRICING.llamaindex.models.map((model) => (
                    <SelectItem
                      key={`${model.parse_mode}:${model.model}`}
                      value={`${model.parse_mode}:${model.model}`}
                    >
                      {model.detailedDescription}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Reducto */}
        <div className="pb-4 border-b">
          <div className="flex items-center mb-3 gap-2">
            <ProviderLabel
              provider="reducto"
              size={20}
              className="gap-2"
              nameClassName="text-sm font-medium"
            />
            <span className="text-xs text-gray-500">(optional)</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Left: API Key */}
            <div>
              <Label htmlFor="reducto-key" className="text-xs text-gray-600 mb-2 block">
                API Key
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
            {/* Right: Mode */}
            <div>
              <Label htmlFor="reducto-mode" className="text-xs text-gray-600 mb-2 block">
                Model
              </Label>
              <Select
                value={configs.reducto?.mode}
                onValueChange={(value) => {
                  handleFullConfigChange("reducto", {
                    mode: value,
                    summarize_figures: value === "complex",
                  });
                }}
                disabled={disabled}
              >
                <SelectTrigger id="reducto-mode">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PRICING.reducto.models.map((model) => (
                    <SelectItem key={model.mode} value={model.mode}>
                      {model.detailedDescription}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* LandingAI */}
        <div>
          <div className="flex items-center mb-3 gap-2">
            <ProviderLabel
              provider="landingai"
              size={20}
              className="gap-2"
              nameClassName="text-sm font-medium"
            />
            <span className="text-xs text-gray-500">(optional)</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Left: API Key */}
            <div>
              <Label htmlFor="landingai-key" className="text-xs text-gray-600 mb-2 block">
                API Key
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
            {/* Right: Model */}
            <div>
              <Label htmlFor="landingai-model" className="text-xs text-gray-600 mb-2 block">
                Model
              </Label>
              <Select value="dpt-2" disabled>
                <SelectTrigger id="landingai-model">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="dpt-2">
                    {PRICING.landingai.models[0].detailedDescription}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </div>

      <p className="text-sm text-gray-500 mt-4">
        Provide at least one API key to enable PDF parsing. Only providers with
        keys will be run.
      </p>
    </div>
  );
}
