import type {
  LlamaIndexConfig,
  ReductoConfig,
  LandingAIConfig,
  ModelOption,
  ProviderPricingInfo,
} from "@/types/api";

export type ProviderPricingMap = Record<string, ProviderPricingInfo>;

// Preset configurations for battle page
export const STANDARD_PRESET = {
  llamaindex: "agentic",
  reducto: "standard",
  landingai: "dpt-2-mini",
} as const;

export const ADVANCE_PRESET = {
  llamaindex: "agentic-plus",
  reducto: "complex",
  landingai: "dpt-2",
} as const;

export type PresetMode = "standard" | "advance" | "custom";

export function getDefaultBattleConfigs() {
  return {
    llamaindex: {
      mode: "agentic",
      parse_mode: "parse_page_with_agent",
      model: "openai-gpt-4-1-mini",
    } as LlamaIndexConfig,
    reducto: {
      mode: "standard",
      summarize_figures: false,
    } as ReductoConfig,
    landingai: {
      mode: "dpt-2-mini",
      model: "dpt-2-mini",
    } as LandingAIConfig,
  };
}

export function llamaIndexConfigToValue(config?: LlamaIndexConfig): string {
  return config?.mode || "";
}

export function reductoConfigToValue(config?: ReductoConfig): string {
  return config?.mode || "";
}

export function landingaiConfigToValue(config?: LandingAIConfig): string {
  return config?.mode || "";
}

const PROVIDER_FALLBACK_LABELS: Record<string, string> = {
  llamaindex: "Agentic",
  reducto: "Standard",
  landingai: "DPT-2",
};

function matchesConfig(option: ModelOption, config?: Record<string, any>): boolean {
  if (!config) return false;
  const optionConfig = option.config || {};

  if (optionConfig.mode && config.mode && optionConfig.mode === config.mode) {
    return true;
  }

  return Object.entries(optionConfig).every(([key, value]) => {
    if (key === "mode") {
      return !config.mode || config.mode === value;
    }
    return config[key] === value;
  });
}

export function getModelOptionForConfig(
  provider: string,
  config: Record<string, any> | undefined,
  pricingMap?: ProviderPricingMap | null
): ModelOption | undefined {
  if (!pricingMap || !config) return undefined;
  const providerInfo = pricingMap[provider];
  if (!providerInfo) return undefined;
  return providerInfo.models.find((option) => matchesConfig(option, config));
}

export function getModelOptionByLabel(
  provider: string,
  label: string,
  pricingMap?: ProviderPricingMap | null
): ModelOption | undefined {
  if (!pricingMap) return undefined;
  const providerInfo = pricingMap[provider];
  if (!providerInfo) return undefined;
  return providerInfo.models.find((option) => option.label === label);
}

export function formatOptionDescription(option: ModelOption): string {
  return `${option.label} - $${option.usd_per_page.toFixed(3)}/page`;
}

export function getFallbackLabel(provider: string): string {
  return PROVIDER_FALLBACK_LABELS[provider] || provider;
}

/**
 * Detect which preset (if any) matches the current config selection
 */
export function detectPresetFromConfigs(configs: {
  llamaindex: LlamaIndexConfig;
  reducto: ReductoConfig;
  landingai: LandingAIConfig;
}): PresetMode {
  const llamaMode = configs.llamaindex?.mode || "";
  const reductoMode = configs.reducto?.mode || "";
  const landingaiMode = configs.landingai?.mode || "";

  // Check if matches standard preset
  if (
    llamaMode === STANDARD_PRESET.llamaindex &&
    reductoMode === STANDARD_PRESET.reducto &&
    landingaiMode === STANDARD_PRESET.landingai
  ) {
    return "standard";
  }

  // Check if matches advance preset
  if (
    llamaMode === ADVANCE_PRESET.llamaindex &&
    reductoMode === ADVANCE_PRESET.reducto &&
    landingaiMode === ADVANCE_PRESET.landingai
  ) {
    return "advance";
  }

  // Otherwise it's custom
  return "custom";
}

/**
 * Get full configs for a given preset mode
 */
export function getConfigsForPreset(
  preset: "standard" | "advance",
  pricing?: ProviderPricingMap | null
): {
  llamaindex: LlamaIndexConfig;
  reducto: ReductoConfig;
  landingai: LandingAIConfig;
} | null {
  if (!pricing) return null;

  const presetModes = preset === "standard" ? STANDARD_PRESET : ADVANCE_PRESET;

  // Find the model options for each preset mode
  const llamaOption = pricing.llamaindex?.models.find(
    (m) => m.value === presetModes.llamaindex
  );
  const reductoOption = pricing.reducto?.models.find(
    (m) => m.value === presetModes.reducto
  );
  const landingaiOption = pricing.landingai?.models.find(
    (m) => m.value === presetModes.landingai
  );

  if (!llamaOption || !reductoOption || !landingaiOption) {
    return null;
  }

  return {
    llamaindex: llamaOption.config as LlamaIndexConfig,
    reducto: reductoOption.config as ReductoConfig,
    landingai: landingaiOption.config as LandingAIConfig,
  };
}
