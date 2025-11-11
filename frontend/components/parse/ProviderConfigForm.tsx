"use client";

import { useState, useEffect } from "react";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Settings } from "lucide-react";
import { ProviderLabel } from "@/components/providers/ProviderLabel";

const CONFIG_STORAGE_KEY = "ragrace_parse_configs";
const SELECTION_STORAGE_KEY = "ragrace_parse_selected_providers";

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

interface ProviderConfigFormProps {
  onConfigsChange: (configs: ProviderConfigs) => void;
  onSelectionChange: (selected: string[]) => void;
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
        credits_per_page: 10,
        description: "Agentic",
        detailedDescription: "Agentic - 10 credits/page ($0.010/page)",
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

export function ProviderConfigForm({
  onConfigsChange,
  onSelectionChange,
  disabled = false,
}: ProviderConfigFormProps) {
  const [selectedProviders, setSelectedProviders] = useState<string[]>([
    "llamaindex",
    "reducto",
    "landingai",
  ]);
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

  // Load configs and selection from localStorage on mount
  useEffect(() => {
    try {
      const storedConfigs = localStorage.getItem(CONFIG_STORAGE_KEY);
      if (storedConfigs) {
        const parsedConfigs = JSON.parse(storedConfigs) as ProviderConfigs;
        setConfigs(parsedConfigs);
        onConfigsChange(parsedConfigs);
      } else {
        // Save default configs
        localStorage.setItem(CONFIG_STORAGE_KEY, JSON.stringify(configs));
        onConfigsChange(configs);
      }

      const storedSelection = localStorage.getItem(SELECTION_STORAGE_KEY);
      if (storedSelection) {
        const parsedSelection = JSON.parse(storedSelection) as string[];
        setSelectedProviders(parsedSelection);
        onSelectionChange(parsedSelection);
      } else {
        // Save default selection
        localStorage.setItem(SELECTION_STORAGE_KEY, JSON.stringify(selectedProviders));
        onSelectionChange(selectedProviders);
      }
    } catch (error) {
      console.error("Failed to load from localStorage:", error);
    }
  }, []);

  const handleProviderToggle = (provider: string) => {
    const newSelection = selectedProviders.includes(provider)
      ? selectedProviders.filter((p) => p !== provider)
      : [...selectedProviders, provider];

    setSelectedProviders(newSelection);

    try {
      localStorage.setItem(SELECTION_STORAGE_KEY, JSON.stringify(newSelection));
    } catch (error) {
      console.error("Failed to save selection to localStorage:", error);
    }

    onSelectionChange(newSelection);
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

    onConfigsChange(newConfigs);
  };

  return (
    <div className="border rounded-lg p-6 bg-card">
      <div className="flex items-center gap-2 mb-4">
        <Settings className="h-5 w-5 text-gray-500" />
        <h2 className="text-lg font-semibold">Provider Configuration</h2>
      </div>

      <div className="space-y-4">
        {/* LlamaIndex */}
        <div className="pb-4 border-b">
          <div className="flex items-center mb-3 gap-2">
            <Checkbox
              id="provider-llamaindex"
              checked={selectedProviders.includes("llamaindex")}
              onCheckedChange={() => handleProviderToggle("llamaindex")}
              disabled={disabled}
            />
            <ProviderLabel
              provider="llamaindex"
              size={20}
              className="gap-2"
              nameClassName="text-sm font-medium"
            />
          </div>
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
              disabled={disabled || !selectedProviders.includes("llamaindex")}
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

        {/* Reducto */}
        <div className="pb-4 border-b">
          <div className="flex items-center mb-3 gap-2">
            <Checkbox
              id="provider-reducto"
              checked={selectedProviders.includes("reducto")}
              onCheckedChange={() => handleProviderToggle("reducto")}
              disabled={disabled}
            />
            <ProviderLabel
              provider="reducto"
              size={20}
              className="gap-2"
              nameClassName="text-sm font-medium"
            />
          </div>
          <div>
            <Label htmlFor="reducto-mode" className="text-xs text-gray-600 mb-2 block">
              Mode
            </Label>
            <Select
              value={configs.reducto?.mode}
              onValueChange={(value) => {
                handleFullConfigChange("reducto", {
                  mode: value,
                  summarize_figures: value === "complex",
                });
              }}
              disabled={disabled || !selectedProviders.includes("reducto")}
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

        {/* LandingAI */}
        <div>
          <div className="flex items-center mb-3 gap-2">
            <Checkbox
              id="provider-landingai"
              checked={selectedProviders.includes("landingai")}
              onCheckedChange={() => handleProviderToggle("landingai")}
              disabled={disabled}
            />
            <ProviderLabel
              provider="landingai"
              size={20}
              className="gap-2"
              nameClassName="text-sm font-medium"
            />
          </div>
          <div>
            <Label htmlFor="landingai-model" className="text-xs text-gray-600 mb-2 block">
              Model
            </Label>
            <Select
              value="dpt-2"
              disabled={disabled || !selectedProviders.includes("landingai")}
            >
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
  );
}
