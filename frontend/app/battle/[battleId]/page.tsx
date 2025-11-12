"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Loader2, Trophy, Minus, Users } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { MarkdownViewer } from "@/components/parse/MarkdownViewer";
import { CostDisplay } from "@/components/parse/CostDisplay";
import { ProviderLabel } from "@/components/providers/ProviderLabel";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { getProviderDisplayName } from "@/lib/providerMetadata";
import { getDefaultBattleConfigs, getModelOptionForConfig, getFallbackLabel } from "@/lib/modelUtils";
import { useProviderPricing } from "@/hooks/useProviderPricing";
import type { BattleDetailResponse, LlamaIndexConfig, ReductoConfig } from "@/types/api";

export default function BattleDetailPage() {
  const params = useParams();
  const router = useRouter();
  const battleId = params.battleId as string;

  const [battle, setBattle] = useState<BattleDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { pricingMap } = useProviderPricing();

  useEffect(() => {
    loadBattle();
  }, [battleId]);

  const loadBattle = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.getBattleDetail(battleId);
      setBattle(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load battle");
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  const isWinner = (label: string) => {
    if (!battle?.feedback?.preferred_labels) return false;
    return battle.feedback.preferred_labels.includes(label);
  };

  const getWinnerStatus = () => {
    if (!battle?.feedback?.preferred_labels) return null;
    const labels = battle.feedback.preferred_labels;
    if (labels.length === 0) return "both_bad";
    if (labels.length === battle.providers.length) return "both_good";
    return "single_winner";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error || !battle) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-red-600 dark:text-red-400">
              {error || "Battle not found"}
            </p>
          </div>
          <Button onClick={() => router.push("/battle")} className="mt-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Battle
          </Button>
        </div>
      </div>
    );
  }

  const winnerStatus = getWinnerStatus();
  const pageNumber = battle.page_number;
  const sortedProviders = [...battle.providers].sort((a, b) => a.label.localeCompare(b.label));

  // Extract model configs from metadata
  const modelConfigs = {
    llamaindex: getDefaultBattleConfigs().llamaindex,
    reducto: getDefaultBattleConfigs().reducto,
  };

  // Update configs from battle metadata
  if (battle.provider_configs) {
    if (battle.provider_configs.llamaindex) {
      modelConfigs.llamaindex = battle.provider_configs.llamaindex as LlamaIndexConfig;
    }
    if (battle.provider_configs.reducto) {
      modelConfigs.reducto = battle.provider_configs.reducto as ReductoConfig;
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div>
        <Button
          variant="ghost"
          onClick={() => router.push("/battle")}
          className="mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Battle
        </Button>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {battle.original_name}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Page {pageNumber} • {formatDate(battle.created_at)}
            </p>
          </div>

          {winnerStatus && (
            <div className="flex items-center gap-2">
              {winnerStatus === "both_good" && (
                <>
                  <Users className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  <span className="font-medium text-blue-600 dark:text-blue-400">
                    Both Good
                  </span>
                </>
              )}
              {winnerStatus === "both_bad" && (
                <>
                  <Minus className="h-5 w-5 text-gray-500 dark:text-gray-400" />
                  <span className="font-medium text-gray-500 dark:text-gray-400">
                    Both Bad
                  </span>
                </>
              )}
              {winnerStatus === "single_winner" && (
                <>
                  <Trophy className="h-5 w-5 text-green-600 dark:text-green-400" />
                  <span className="font-medium text-green-600 dark:text-green-400">
                    Winner Selected
                  </span>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* PDF Viewer */}
      <div>
        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="text-2xl font-bold tracking-tight">
              Original PDF - Page {pageNumber}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="flex justify-center bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden">
              <iframe
                src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/parse/battle-pdf/${battleId}#navpanes=0&toolbar=0`}
                className="w-full h-[700px] border-0"
                title="Battle PDF (Single Page)"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Feedback Comment */}
      {battle.feedback?.comment && (
        <div>
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Feedback:
            </p>
            <p className="text-gray-600 dark:text-gray-400">
              {battle.feedback.comment}
            </p>
          </div>
        </div>
      )}

      {/* Provider Results */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">Battle Results</h2>
        <div className="grid gap-6 md:grid-cols-2 items-start">
          {sortedProviders.map((provider) => {
            const assignment = battle.assignments.find((a) => a.label === provider.label);
            const isThisWinner = isWinner(provider.label);
            const isAllBad = winnerStatus === "both_bad";
            const markdown = provider.content.pages.find((p) => p.page_number === pageNumber)?.markdown
              || provider.content.pages[0]?.markdown;

            const displayName = getProviderDisplayName(assignment?.provider || provider.provider);

            // Get model display name and pricing
            const providerName = assignment?.provider || provider.provider;
            let modelDisplayName = "";
            let modelPricing = "";

            if (providerName === "llamaindex" && modelConfigs.llamaindex) {
              const option = getModelOptionForConfig("llamaindex", modelConfigs.llamaindex, pricingMap);
              modelDisplayName = option?.label || getFallbackLabel("llamaindex");
              if (option) {
                modelPricing = `$${option.usd_per_page.toFixed(3)}/page`;
              }
            } else if (providerName === "reducto" && modelConfigs.reducto) {
              const option = getModelOptionForConfig("reducto", modelConfigs.reducto, pricingMap);
              modelDisplayName = option?.label || getFallbackLabel("reducto");
              if (option) {
                modelPricing = `$${option.usd_per_page.toFixed(3)}/page`;
              }
            }

            const cardClass = cn(
              "transition-all",
              isThisWinner && "border-emerald-500 bg-emerald-50/60 dark:bg-emerald-950/20",
              !isThisWinner && !isAllBad && battle.feedback && "border-red-400 bg-red-50/60 dark:bg-red-950/20",
              isAllBad && "border-red-500 bg-red-50/60 dark:bg-red-950/20"
            );

            const title = (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <ProviderLabel provider={assignment?.provider || provider.provider} size={28} />
                  {modelDisplayName && (
                    <>
                      <span className="text-gray-400">•</span>
                      <div className="text-base font-medium text-gray-700 dark:text-gray-300">
                        {modelDisplayName} ({modelPricing})
                      </div>
                    </>
                  )}
                </div>
                {isThisWinner && (
                  <Trophy className="h-5 w-5 text-green-600 dark:text-green-400" />
                )}
              </div>
            );

            const footer = (provider.cost_usd !== null && provider.cost_usd !== undefined) ? (
              <CostDisplay
                cost={{
                  provider: provider.provider,
                  credits: provider.cost_credits || 0,
                  usd_per_credit: provider.cost_usd / (provider.cost_credits || 1),
                  total_usd: provider.cost_usd,
                  details: {},
                }}
                providerName={displayName}
              />
            ) : (
              <p className="text-xs text-gray-500">Cost data unavailable</p>
            );

            return (
              <MarkdownViewer
                key={provider.label}
                title={title}
                markdown={markdown}
                cardClassName={cardClass}
                footer={footer}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}
