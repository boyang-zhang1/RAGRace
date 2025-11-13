"use client";

import { useState, useEffect } from "react";
import { LlamaIndexConfig, ReductoConfig, LandingAIConfig } from "@/types/api";
import {
  ProviderPricingMap,
  llamaIndexConfigToValue,
  reductoConfigToValue,
  landingaiConfigToValue,
  getModelOptionForConfig,
  formatOptionDescription,
  getFallbackLabel,
  PresetMode,
  detectPresetFromConfigs,
  getConfigsForPreset,
} from "@/lib/modelUtils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { ProviderLabel } from "@/components/providers/ProviderLabel";

interface ModelSelectionCardProps {
  selectedConfigs: {
    llamaindex: LlamaIndexConfig;
    reducto: ReductoConfig;
    landingai: LandingAIConfig;
  };
  onConfigChange?: (configs: {
    llamaindex: LlamaIndexConfig;
    reducto: ReductoConfig;
    landingai: LandingAIConfig;
  }) => void;
  readOnly?: boolean;
  pricing?: ProviderPricingMap | null;
  pricingLoading?: boolean;
  pricingError?: string | null;
}

export function ModelSelectionCard({
  selectedConfigs,
  onConfigChange,
  readOnly = false,
  pricing,
  pricingLoading = false,
  pricingError = null,
}: ModelSelectionCardProps) {
  // Track the current preset mode (standard, advance, or custom)
  const [presetMode, setPresetMode] = useState<PresetMode>("standard");

  // Detect which preset (if any) matches the current configs
  useEffect(() => {
    const detectedPreset = detectPresetFromConfigs(selectedConfigs);
    setPresetMode(detectedPreset);
  }, [selectedConfigs]);

  // Handle toggle change between standard and advance
  const handlePresetToggle = (checked: boolean) => {
    if (readOnly || !onConfigChange || !pricing) return;

    const newPreset = checked ? "advance" : "standard";
    const newConfigs = getConfigsForPreset(newPreset, pricing);

    if (newConfigs) {
      onConfigChange(newConfigs);
    }
  };

  const handleLlamaIndexChange = (value: string) => {
    if (readOnly || !onConfigChange) return;
    const option = pricing?.llamaindex?.models.find((model) => model.value === value);
    if (!option) return;
    onConfigChange({
      ...selectedConfigs,
      llamaindex: option.config as LlamaIndexConfig,
    });
  };

  const handleReductoChange = (value: string) => {
    if (readOnly || !onConfigChange) return;
    const option = pricing?.reducto?.models.find((model) => model.value === value);
    if (!option) return;
    onConfigChange({
      ...selectedConfigs,
      reducto: option.config as ReductoConfig,
    });
  };

  const handleLandingAIChange = (value: string) => {
    if (readOnly || !onConfigChange) return;
    const option = pricing?.landingai?.models.find((model) => model.value === value);
    if (!option) return;
    onConfigChange({
      ...selectedConfigs,
      landingai: option.config as LandingAIConfig,
    });
  };

  if (!pricing) {
    return (
      <div className="rounded-xl border border-purple-200 bg-purple-50/70 dark:border-purple-900/50 dark:bg-purple-950/30 px-4 pt-2 pb-4">
        <h3 className="text-sm font-semibold text-purple-900 dark:text-purple-100 mb-3">
          {readOnly ? "Models used in this battle" : "Model Selection"}
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {pricingLoading
            ? "Loading provider pricing..."
            : pricingError || "Pricing data unavailable."}
        </p>
      </div>
    );
  }

  const llamaOptions = pricing.llamaindex?.models ?? [];
  const reductoOptions = pricing.reducto?.models ?? [];
  const landingaiOptions = pricing.landingai?.models ?? [];

  const llamaSelection = getModelOptionForConfig(
    "llamaindex",
    selectedConfigs.llamaindex,
    pricing
  );
  const reductoSelection = getModelOptionForConfig(
    "reducto",
    selectedConfigs.reducto,
    pricing
  );
  const landingaiSelection = getModelOptionForConfig(
    "landingai",
    selectedConfigs.landingai,
    pricing
  );

  return (
    <div className="rounded-xl border border-purple-200 bg-purple-50/70 dark:border-purple-900/50 dark:bg-purple-950/30 px-4 pt-2 pb-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-purple-900 dark:text-purple-100">
          {readOnly ? "Models used in this battle" : "Model Selection"}
        </h3>

        {/* Preset toggle - only show in edit mode */}
        {!readOnly && (
          <div className="flex items-center gap-3">
            {presetMode === "custom" && (
              <span className="text-sm text-purple-600 dark:text-purple-400 font-medium">
                (Custom)
              </span>
            )}
            <div className="inline-flex rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-800 p-1">
              <button
                onClick={() => handlePresetToggle(false)}
                disabled={!pricing}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
                  presetMode === "standard"
                    ? "bg-white dark:bg-gray-700 text-purple-600 dark:text-purple-400 shadow-sm"
                    : "text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                }`}
              >
                Standard
              </button>
              <button
                onClick={() => handlePresetToggle(true)}
                disabled={!pricing}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
                  presetMode === "advance"
                    ? "bg-white dark:bg-gray-700 text-purple-600 dark:text-purple-400 shadow-sm"
                    : "text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                }`}
              >
                Advance
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* LlamaIndex Column */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 mb-2">
            <ProviderLabel provider="llamaindex" size={20} className="gap-2" nameClassName="text-sm font-medium" />
          </div>
          {readOnly ? (
            <div className="text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-950 rounded-md border border-gray-200 dark:border-gray-700 px-3 py-2">
              {llamaSelection?.label || getFallbackLabel("llamaindex")}
            </div>
          ) : (
            <Select
              value={llamaIndexConfigToValue(selectedConfigs.llamaindex)}
              onValueChange={handleLlamaIndexChange}
              disabled={!llamaOptions.length}
            >
              <SelectTrigger id="llamaindex-model" className="bg-white dark:bg-gray-950">
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
          )}
        </div>

        {/* Reducto Column */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 mb-2">
            <ProviderLabel provider="reducto" size={20} className="gap-2" nameClassName="text-sm font-medium" />
          </div>
          {readOnly ? (
            <div className="text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-950 rounded-md border border-gray-200 dark:border-gray-700 px-3 py-2">
              {reductoSelection?.label || getFallbackLabel("reducto")}
            </div>
          ) : (
            <Select
              value={reductoConfigToValue(selectedConfigs.reducto)}
              onValueChange={handleReductoChange}
              disabled={!reductoOptions.length}
            >
              <SelectTrigger id="reducto-mode" className="bg-white dark:bg-gray-950">
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
          )}
        </div>

        {/* LandingAI Column */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 mb-2">
            <ProviderLabel provider="landingai" size={20} className="gap-2" nameClassName="text-sm font-medium" />
          </div>
          {readOnly ? (
            <div className="text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-950 rounded-md border border-gray-200 dark:border-gray-700 px-3 py-2">
              {landingaiSelection?.label || getFallbackLabel("landingai")}
            </div>
          ) : (
            <Select
              value={landingaiConfigToValue(selectedConfigs.landingai)}
              onValueChange={handleLandingAIChange}
              disabled={!landingaiOptions.length}
            >
              <SelectTrigger id="landingai-model" className="bg-white dark:bg-gray-950">
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
          )}
        </div>
      </div>
    </div>
  );
}
