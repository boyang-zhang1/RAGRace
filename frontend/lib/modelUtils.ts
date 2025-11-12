import type {
  LlamaIndexConfig,
  ReductoConfig,
  LandingAIConfig,
  ModelOption,
  ProviderPricingInfo,
} from "@/types/api";

export type ProviderPricingMap = Record<string, ProviderPricingInfo>;

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
      mode: "dpt-2",
      model: "dpt-2",
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
  return `${option.label} - ${option.credits_per_page} credits/page ($${option.usd_per_page.toFixed(3)}/page)`;
}

export function getFallbackLabel(provider: string): string {
  return PROVIDER_FALLBACK_LABELS[provider] || provider;
}
