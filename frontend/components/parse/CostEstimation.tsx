"use client";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DollarSign, FileText, AlertCircle } from "lucide-react";
import { ProviderLabel } from "@/components/providers/ProviderLabel";

interface ProviderCost {
  credits_per_page: number;
  total_credits: number;
  usd_per_credit: number;
  total_usd: number;
}

interface CostEstimationProps {
  pageCount: number;
  providers: string[];
  configs: Record<string, any>;
  onConfirm: () => void;
  disabled?: boolean;
}

// Pricing information (must match ApiKeyForm)
const PRICING = {
  llamaindex: {
    usd_per_credit: 0.001,
    models: [
      {
        parse_mode: "parse_page_with_llm",
        model: "default",
        credits_per_page: 3,
      },
      {
        parse_mode: "parse_page_with_agent",
        model: "openai-gpt-4-1-mini",
        credits_per_page: 20,
      },
      {
        parse_mode: "parse_page_with_agent",
        model: "anthropic-sonnet-4.0",
        credits_per_page: 90,
      },
    ],
  },
  reducto: {
    usd_per_credit: 0.015,
    models: [
      { mode: "standard", summarize_figures: false, credits_per_page: 1 },
      { mode: "complex", summarize_figures: true, credits_per_page: 2 },
    ],
  },
  landingai: {
    usd_per_credit: 0.01,
    models: [{ model: "dpt-2", credits_per_page: 3 }],
  },
};

export function CostEstimation({
  pageCount,
  providers,
  configs,
  onConfirm,
  disabled = false,
}: CostEstimationProps) {
  // Calculate cost for each provider
  const calculateProviderCost = (
    provider: string,
    config: any
  ): ProviderCost | null => {
    const providerPricing = PRICING[provider as keyof typeof PRICING];
    if (!providerPricing) return null;

    let model;
    if (provider === "llamaindex") {
      model = providerPricing.models.find(
        (m: any) =>
          m.parse_mode === config.parse_mode && m.model === config.model
      );
    } else if (provider === "reducto") {
      model = providerPricing.models.find((m: any) => m.mode === config.mode);
    } else if (provider === "landingai") {
      model = providerPricing.models[0];
    }

    if (!model) return null;

    const total_credits = pageCount * model.credits_per_page;
    const total_usd = total_credits * providerPricing.usd_per_credit;

    return {
      credits_per_page: model.credits_per_page,
      total_credits,
      usd_per_credit: providerPricing.usd_per_credit,
      total_usd,
    };
  };

  // Calculate costs for all providers
  const providerCosts: Record<string, ProviderCost> = {};
  let totalCost = 0;

  providers.forEach((provider) => {
    const config = configs[provider];
    if (config) {
      const cost = calculateProviderCost(provider, config);
      if (cost) {
        providerCosts[provider] = cost;
        totalCost += cost.total_usd;
      }
    }
  });

  return (
    <Card className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-indigo-200">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center gap-2 pb-2 border-b border-indigo-200">
          <FileText className="h-5 w-5 text-indigo-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Cost Estimation
          </h3>
          <span className="ml-auto text-sm text-gray-600">
            {pageCount} {pageCount === 1 ? "page" : "pages"}
          </span>
        </div>

        {/* Provider breakdown */}
        <div className="space-y-3">
          {providers.map((provider) => {
            const cost = providerCosts[provider];
            if (!cost) return null;

            return (
              <div
                key={provider}
                className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200"
              >
                <div className="flex items-center gap-3">
                  <ProviderLabel
                    provider={provider}
                    size={24}
                    className="gap-2"
                  />
                  <div className="text-sm text-gray-600">
                    {cost.credits_per_page} credits/page × {pageCount} pages
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900">
                    ${cost.total_usd.toFixed(3)}
                  </div>
                  <div className="text-xs text-gray-500">
                    {cost.total_credits.toFixed(0)} credits
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Total cost */}
        <div className="flex items-center justify-between pt-3 border-t border-indigo-200">
          <div className="flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-indigo-600" />
            <span className="font-semibold text-gray-900">Total Cost</span>
          </div>
          <div className="text-xl font-bold text-indigo-600">
            ${totalCost.toFixed(3)}
          </div>
        </div>

        {/* Warning if cost is high */}
        {totalCost > 1.0 && (
          <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-amber-800">
              This operation will cost more than $1.00. Please confirm before
              proceeding.
            </p>
          </div>
        )}

        {/* Confirm button */}
        <Button
          onClick={onConfirm}
          disabled={disabled}
          className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium"
          size="lg"
        >
          {disabled ? "Parsing..." : "Confirm and Parse"}
        </Button>
      </div>
    </Card>
  );
}
