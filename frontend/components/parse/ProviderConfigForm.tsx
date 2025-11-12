"use client";

import { useState, useEffect } from "react";
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
import type { LlamaIndexConfig, ReductoConfig, LandingAIConfig } from "@/types/api";
import {
  ProviderPricingMap,
  formatOptionDescription,
  llamaIndexConfigToValue,
  reductoConfigToValue,
  getModelOptionForConfig,
} from "@/lib/modelUtils";

const CONFIG_STORAGE_KEY = "ragrace_parse_configs";
const SELECTION_STORAGE_KEY = "ragrace_parse_selected_providers";

interface ProviderConfigs {
  llamaindex?: LlamaIndexConfig;
  reducto?: ReductoConfig;
  landingai?: LandingAIConfig;
}

interface ProviderConfigFormProps {
  onConfigsChange: (configs: ProviderConfigs) => void;
  onSelectionChange: (selected: string[]) => void;
  disabled?: boolean;
  pricing?: ProviderPricingMap | null;
  pricingLoading?: boolean;
  pricingError?: string | null;
}

export function ProviderConfigForm({
  onConfigsChange,
  onSelectionChange,
  disabled = false,
  pricing,
  pricingLoading = false,
  pricingError = null,
}: ProviderConfigFormProps) {
  const [selectedProviders, setSelectedProviders] = useState<string[]>([
    "llamaindex",
    "reducto",
    "landingai",
  ]);
  const [configs, setConfigs] = useState<ProviderConfigs>({
    llamaindex: {
      mode: "agentic",
      parse_mode: "parse_page_with_agent",
      model: "openai-gpt-4-1-mini",
    },
    reducto: {
      mode: "standard",
      summarize_figures: false,
    },
    landingai: {
      mode: "dpt-2",
      model: "dpt-2",
    },
  });

  const llamaOptions = pricing?.llamaindex?.models ?? [];
  const reductoOptions = pricing?.reducto?.models ?? [];
  const landingaiOptions = pricing?.landingai?.models ?? [];
  const landingaiValue =
    landingaiOptions.find((option) => option.value === configs.landingai?.mode)?.value ||
    configs.landingai?.mode ||
    landingaiOptions[0]?.value ||
    "";

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

  useEffect(() => {
    if (!pricing) return;

    setConfigs((current) => {
      let changed = false;
      const next: ProviderConfigs = { ...current };

      const updateProvider = (provider: keyof ProviderConfigs) => {
        const providerKey = provider as string;
        const options = pricing?.[providerKey]?.models ?? [];
        if (!options.length) {
          return;
        }

        const matched = getModelOptionForConfig(providerKey, next[provider], pricing);
        const target = matched ?? options[0];
        if (!target) {
          return;
        }

        const targetConfig = target.config as Record<string, any>;
        const currentConfig = next[provider] as Record<string, any> | undefined;
        const configsMatch = currentConfig && Object.keys({ ...currentConfig, ...targetConfig }).every(
          (key) => currentConfig[key] === targetConfig[key]
        );

        if (!configsMatch) {
          next[provider] = targetConfig as any;
          changed = true;
        }
      };

      updateProvider("llamaindex");
      updateProvider("reducto");
      updateProvider("landingai");

      if (!changed) {
        return current;
      }

      try {
        localStorage.setItem(CONFIG_STORAGE_KEY, JSON.stringify(next));
      } catch (error) {
        console.error("Failed to save configs to localStorage:", error);
      }

      onConfigsChange(next);
      return next;
    });
  }, [pricing]);

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
    const nextValue = updates.mode ? updates : { ...configs[provider], ...updates };
    const newConfigs = {
      ...configs,
      [provider]: nextValue,
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

      <div className="grid grid-cols-3 gap-6">
        {/* LlamaIndex Column */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 mb-2">
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
          <Select
            value={configs.llamaindex ? llamaIndexConfigToValue(configs.llamaindex) : ""}
            onValueChange={(value) => {
              const option = llamaOptions.find((model) => model.value === value);
              if (option) {
                handleFullConfigChange("llamaindex", option.config);
              }
            }}
            disabled={
              disabled ||
              !selectedProviders.includes("llamaindex") ||
              llamaOptions.length === 0
            }
          >
            <SelectTrigger id="llamaindex-model">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {llamaOptions.map((model) => (
                <SelectItem key={model.value} value={model.value}>
                  {formatOptionDescription(model)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {llamaOptions.length === 0 && (
            <p className="mt-2 text-xs text-gray-500">
              {pricingLoading
                ? "Loading pricing..."
                : pricingError || "Pricing data unavailable."}
            </p>
          )}
        </div>

        {/* Reducto Column */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 mb-2">
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
          <Select
            value={configs.reducto ? reductoConfigToValue(configs.reducto) : ""}
            onValueChange={(value) => {
              const option = reductoOptions.find((model) => model.value === value);
              if (option) {
                handleFullConfigChange("reducto", option.config);
              }
            }}
            disabled={
              disabled ||
              !selectedProviders.includes("reducto") ||
              reductoOptions.length === 0
            }
          >
            <SelectTrigger id="reducto-mode">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {reductoOptions.map((model) => (
                <SelectItem key={model.value} value={model.value}>
                  {formatOptionDescription(model)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {reductoOptions.length === 0 && (
            <p className="mt-2 text-xs text-gray-500">
              {pricingLoading
                ? "Loading pricing..."
                : pricingError || "Pricing data unavailable."}
            </p>
          )}
        </div>

        {/* LandingAI Column */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 mb-2">
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
          <Select
            value={landingaiValue || undefined}
            onValueChange={(value) => {
              const option = landingaiOptions.find((model) => model.value === value);
              if (option) {
                handleFullConfigChange("landingai", option.config);
              }
            }}
            disabled={
              disabled ||
              !selectedProviders.includes("landingai") ||
              landingaiOptions.length === 0
            }
          >
            <SelectTrigger id="landingai-model">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {landingaiOptions.map((model) => (
                <SelectItem key={model.value} value={model.value}>
                  {formatOptionDescription(model)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {landingaiOptions.length === 0 && (
            <p className="mt-2 text-xs text-gray-500">
              {pricingLoading
                ? "Loading pricing..."
                : pricingError || "Pricing data unavailable."}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
