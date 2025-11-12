"use client";

import { useMemo, useState } from "react";
import { FileUploadZone } from "@/components/parse/FileUploadZone";
import { PDFViewer } from "@/components/parse/PDFViewer";
import { PageNavigator } from "@/components/parse/PageNavigator";
import { MarkdownViewer } from "@/components/parse/MarkdownViewer";
import { CostDisplay } from "@/components/parse/CostDisplay";
import { Button } from "@/components/ui/button";
import { Loader2, FileText, ShieldCheck, Sparkles } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import {
  type BattleMetadata,
  type ProviderParseResult,
  type ProviderCost,
} from "@/types/api";
import { getProviderDisplayName } from "@/lib/providerMetadata";
import { ProviderLabel } from "@/components/providers/ProviderLabel";
import { cn } from "@/lib/utils";

type FeedbackChoice = string | "BOTH_GOOD" | "BOTH_BAD";

export default function BattlePage() {
  const [fileId, setFileId] = useState<string | null>(null);
  const [fileName, setFileName] = useState("");
  const [pageCount, setPageCount] = useState<number | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [battlePageNumber, setBattlePageNumber] = useState<number | null>(null);

  const [isUploading, setIsUploading] = useState(false);
  const [isLoadingPageCount, setIsLoadingPageCount] = useState(false);
  const [isParsing, setIsParsing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [parseResults, setParseResults] = useState<Record<string, ProviderParseResult> | null>(null);
  const [battleMeta, setBattleMeta] = useState<BattleMetadata | null>(null);
  const [costResults, setCostResults] = useState<Record<string, ProviderCost> | null>(null);

  const [feedbackChoice, setFeedbackChoice] = useState<FeedbackChoice | null>(null);
  const [feedbackComment, setFeedbackComment] = useState("");
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);
  const [feedbackSuccess, setFeedbackSuccess] = useState(false);
  const [preferredLabels, setPreferredLabels] = useState<string[] | null>(null);

  const assignments = useMemo(
    () => battleMeta?.assignments ?? [],
    [battleMeta]
  );
  const isBattleReady = !!parseResults && assignments.length > 0;
  const isRevealed = preferredLabels !== null;
  const selectedPageForRun = battlePageNumber ?? currentPage;

  const resetBattleState = () => {
    setParseResults(null);
    setBattleMeta(null);
    setCostResults(null);
    setPreferredLabels(null);
    setFeedbackChoice(null);
    setFeedbackComment("");
    setFeedbackSuccess(false);
    setFeedbackError(null);
  };

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setError(null);
    resetBattleState();

    try {
      const upload = await apiClient.uploadPdf(file);
      setFileId(upload.file_id);
      setFileName(upload.filename);
      setCurrentPage(1);
      setBattlePageNumber(null);

      setIsLoadingPageCount(true);
      try {
        const count = await apiClient.getPageCount(upload.file_id);
        setPageCount(count.page_count);
      } finally {
        setIsLoadingPageCount(false);
      }
    } catch (err) {
      console.error("Upload error:", err);
      setError(err instanceof Error ? err.message : "Failed to upload PDF");
    } finally {
      setIsUploading(false);
    }
  };

  const handleRunBattle = async () => {
    if (!fileId) return;
    if (!pageCount) {
      setError("Please wait for the page count before running a battle.");
      return;
    }

    setIsParsing(true);
    setError(null);
    setFeedbackError(null);

    try {
      const data = await apiClient.compareParses({
        fileId,
        pageNumber: currentPage,
        filename: fileName || undefined,
      });

      if (!data.battle) {
        throw new Error("Battle metadata missing. Please try again.");
      }

      setParseResults(data.results);
      setBattleMeta(data.battle);
      setBattlePageNumber(currentPage);
      setPreferredLabels(null);
      setFeedbackChoice(null);
      setFeedbackComment("");
      setFeedbackSuccess(false);
      setCostResults(null);

      try {
        const costData = await apiClient.calculateParseCost(data);
        setCostResults(costData.costs);
      } catch (costErr) {
        console.warn("Cost calculation failed", costErr);
      }
    } catch (err) {
      console.error("Battle parse error:", err);
      setError(err instanceof Error ? err.message : "Failed to run battle");
    } finally {
      setIsParsing(false);
    }
  };

  const handleSubmitFeedback = async () => {
    if (!battleMeta?.battle_id || !feedbackChoice) {
      setFeedbackError("Pick a feedback option before submitting.");
      return;
    }

    setIsSubmittingFeedback(true);
    setFeedbackError(null);

    try {
      const preferred = derivePreferredLabels(feedbackChoice, assignments);
      const response = await submitFeedbackWithRetry({
        battleId: battleMeta.battle_id,
        preferredLabels: preferred,
        comment: feedbackComment.trim() || undefined,
      });

      setPreferredLabels(response.preferred_labels);
      setBattleMeta({
        battle_id: response.battle_id,
        assignments: response.assignments,
      });
      setFeedbackSuccess(true);
    } catch (err) {
      console.error("Feedback error:", err);
      setFeedbackError(err instanceof Error ? err.message : "Failed to save feedback");
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

  const handleReset = () => {
    setFileId(null);
    setFileName("");
    setPageCount(null);
    setCurrentPage(1);
    setBattlePageNumber(null);
    resetBattleState();
  };

  const battleInfo = useMemo(() => {
    if (!isBattleReady || !parseResults) return null;
    return assignments.map((assignment) => {
      const providerResult = parseResults[assignment.provider];
      return {
        assignment,
        providerResult,
        markdown: getPageMarkdown(providerResult, selectedPageForRun),
        cost: costResults?.[assignment.provider],
      };
    });
  }, [assignments, costResults, isBattleReady, parseResults, selectedPageForRun]);

  return (
    <div className="container mx-auto p-6 max-w-full px-8">
      <div className="mb-8 space-y-3">
        <div className="flex items-center gap-3">
          <ShieldCheck className="h-8 w-8 text-blue-500" />
          <div>
            <h1 className="text-3xl font-bold">Parse Battle</h1>
            <p className="text-gray-600 dark:text-gray-400">
              Upload a PDF, pick a single page, and blind-rank two parser outputs before we reveal who&apos;s who.
            </p>
          </div>
        </div>
        <div className="rounded-xl border border-blue-200 bg-blue-50/70 dark:border-blue-900/50 dark:bg-blue-950/30 p-4 flex gap-3 text-sm text-blue-900 dark:text-blue-100">
          <Sparkles className="h-5 w-5 shrink-0" />
          <div>
            <p className="font-semibold">How credits are used</p>
            <p>
              We automatically run LlamaIndex Agentic ($0.010/page) versus Reducto Standard ($0.015/page) on the page you select.
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-md border border-red-200 bg-red-50 p-4 text-red-800 dark:border-red-800 dark:bg-red-950/40 dark:text-red-200">
          {error}
        </div>
      )}

      {!fileId ? (
        <div className="max-w-2xl mx-auto space-y-4">
          <FileUploadZone onUpload={handleUpload} disabled={isUploading} />
          {isUploading && (
            <p className="text-center text-sm text-gray-500 flex items-center justify-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" /> Uploading PDF...
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 border rounded-xl p-4">
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
                <FileText className="h-5 w-5" />
                <span className="font-semibold">{fileName}</span>
              </div>
              {pageCount !== null && (
                <p className="text-sm text-gray-500">
                  {pageCount} {pageCount === 1 ? "page" : "pages"} total • Currently viewing page {currentPage}
                </p>
              )}
              {battlePageNumber && (
                <p className="text-xs text-gray-500">
                  Last battle ran on page {battlePageNumber}
                </p>
              )}
            </div>
            <div className="flex flex-wrap gap-3">
              <Button variant="outline" onClick={handleReset} disabled={isUploading || isParsing}>
                Upload Another PDF
              </Button>
              <Button
                onClick={handleRunBattle}
                disabled={isParsing || isUploading || pageCount === null}
              >
                {isParsing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {battlePageNumber ? "Re-run Battle" : "Run Battle"}
              </Button>
            </div>
          </div>

          {isLoadingPageCount && (
            <div className="rounded-xl border border-dashed border-gray-300 p-6 text-center text-gray-500">
              <Loader2 className="mx-auto mb-3 h-6 w-6 animate-spin text-blue-500" />
              Calculating page count...
            </div>
          )}

          {fileId && (
            <div className="space-y-4">
              <div className="max-w-4xl mx-auto">
                <PDFViewer
                  fileId={fileId}
                  currentPage={currentPage}
                  onPageChange={setCurrentPage}
                  onLoadSuccess={(numPages) => {
                    if (!pageCount) {
                      setPageCount(numPages);
                    }
                  }}
                />
              </div>
              {pageCount && (
                <>
                  <PageNavigator
                    currentPage={currentPage}
                    totalPages={pageCount}
                    onPageChange={setCurrentPage}
                  />
                  <p className="text-center text-sm text-gray-500">
                    We will only parse the page you select to keep cost low.
                  </p>
                </>
              )}
            </div>
          )}

          {isParsing && (
            <div className="rounded-xl border border-blue-200 bg-blue-50 p-6 text-center text-blue-700 dark:border-blue-900 dark:bg-blue-950/30 dark:text-blue-100">
              <Loader2 className="mx-auto mb-4 h-8 w-8 animate-spin" />
              Running both providers on page {currentPage}...
            </div>
          )}

          {isBattleReady && battleInfo && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-semibold">Battle results</h2>
                  <p className="text-sm text-gray-500">
                    Showing blind outputs for page {selectedPageForRun}. Submit feedback to reveal providers.
                  </p>
                </div>
                {battleMeta?.battle_id && (
                  <span className="text-xs text-gray-400">Battle ID: {battleMeta.battle_id}</span>
                )}
              </div>

              <div className="grid gap-6 md:grid-cols-2 items-stretch">
                {battleInfo.map(({ assignment, markdown, providerResult, cost }) => {
                  const label = assignment.label;
                  const provider = assignment.provider;
                  const displayName = getProviderDisplayName(provider);
                  const isPreferred = isRevealed && (preferredLabels?.includes(label) ?? false);
                  const isAllBad = isRevealed && (preferredLabels?.length === 0);
                  const cardClass = cn(
                    "transition-all",
                    !isRevealed && "border-gray-200 dark:border-gray-800",
                    isRevealed && isPreferred && "border-emerald-500 bg-emerald-50/60 dark:bg-emerald-950/20",
                    isRevealed && !isPreferred && !isAllBad && "border-red-400 bg-red-50/60 dark:bg-red-950/20",
                    isRevealed && isAllBad && "border-red-500 bg-red-50/60 dark:bg-red-950/20"
                  );

                  const footer = isRevealed ? (
                    cost ? (
                      <CostDisplay cost={cost} providerName={displayName} />
                    ) : (
                      <p className="text-xs text-gray-500">Cost data unavailable</p>
                    )
                  ) : (
                    <p className="text-xs text-gray-500">
                      Provider + cost unlock after you submit feedback.
                    </p>
                  );

                  const title = isRevealed ? (
                    <div className="flex items-center gap-3">
                      <ProviderLabel provider={provider} size={28} />
                      <div>
                        <div className="text-xl font-semibold">{displayName}</div>
                        <p className="text-sm text-gray-500">Provider {label}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <span className="text-xl font-semibold">Provider {label}</span>
                      <span className="text-xs uppercase tracking-wide text-gray-400">
                        Hidden until feedback
                      </span>
                    </div>
                  );

                  return (
                    <MarkdownViewer
                      key={label}
                      title={title}
                      markdown={markdown}
                      cardClassName={cardClass}
                      footer={footer}
                    />
                  );
                })}
              </div>
            </div>
          )}

          {isBattleReady && (
            <div className="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-6 space-y-4">
              <div>
                <h3 className="text-xl font-semibold">Give your verdict</h3>
                <p className="text-sm text-gray-500">
                  Pick the answer you prefer (or say both are good/bad). You can add a short note to explain why.
                </p>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                {assignments.map((assignment, index) => {
                  const isLeft = index === 0;
                  const buttonLabel = isLeft ? "← Left is better" : "Right is better →";
                  const description = isLeft
                    ? "The left answer is clearer, more accurate, or more useful."
                    : "The right answer is clearer, more accurate, or more useful.";

                  return (
                    <button
                      key={assignment.label}
                      type="button"
                      disabled={feedbackSuccess}
                      onClick={() => setFeedbackChoice(assignment.label)}
                      className={cn(
                        "rounded-xl border p-4 text-left transition",
                        feedbackChoice === assignment.label
                          ? "border-blue-500 bg-blue-50 dark:bg-blue-950/40"
                          : "border-gray-200 hover:border-blue-300"
                      )}
                    >
                      <p className="font-semibold">{buttonLabel}</p>
                      <p className="text-sm text-gray-500">{description}</p>
                    </button>
                  );
                })}
                <button
                  type="button"
                  disabled={feedbackSuccess}
                  onClick={() => setFeedbackChoice("BOTH_GOOD")}
                  className={cn(
                    "rounded-xl border p-4 text-left transition",
                    feedbackChoice === "BOTH_GOOD"
                      ? "border-emerald-500 bg-emerald-50 dark:bg-emerald-950/40"
                      : "border-gray-200 hover:border-emerald-300"
                  )}
                >
                  <p className="font-semibold">Both are good</p>
                  <p className="text-sm text-gray-500">
                    I would happily use either answer.
                  </p>
                </button>
                <button
                  type="button"
                  disabled={feedbackSuccess}
                  onClick={() => setFeedbackChoice("BOTH_BAD")}
                  className={cn(
                    "rounded-xl border p-4 text-left transition",
                    feedbackChoice === "BOTH_BAD"
                      ? "border-red-500 bg-red-50 dark:bg-red-950/40"
                      : "border-gray-200 hover:border-red-300"
                  )}
                >
                  <p className="font-semibold">Both are bad</p>
                  <p className="text-sm text-gray-500">
                    Neither response is usable.
                  </p>
                </button>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Reason (optional)
                </label>
                <textarea
                  value={feedbackComment}
                  onChange={(e) => setFeedbackComment(e.target.value)}
                  placeholder="Let us know why you preferred that answer..."
                  maxLength={500}
                  disabled={feedbackSuccess}
                  className="w-full rounded-lg border border-gray-200 dark:border-gray-800 bg-transparent px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  rows={3}
                />
              </div>

              {feedbackError && (
                <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  {feedbackError}
                </div>
              )}

              {feedbackSuccess && (
                <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
                  Feedback saved. Providers revealed!
                </div>
              )}

              <div className="flex justify-end">
                <Button
                  onClick={handleSubmitFeedback}
                  disabled={
                    !feedbackChoice ||
                    isSubmittingFeedback ||
                    feedbackSuccess ||
                    assignments.length === 0
                  }
                >
                  {isSubmittingFeedback && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Submit feedback
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

async function submitFeedbackWithRetry({
  battleId,
  preferredLabels,
  comment,
}: {
  battleId: string;
  preferredLabels: string[];
  comment?: string;
}) {
  const maxAttempts = 3;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await apiClient.submitBattleFeedback({
        battle_id: battleId,
        preferred_labels: preferredLabels,
        comment,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "";
      const isBattleMissing = /battle run not found/i.test(message);
      const shouldRetry = isBattleMissing && attempt < maxAttempts;

      if (!shouldRetry) {
        throw error;
      }

      await new Promise((resolve) => setTimeout(resolve, attempt * 800));
    }
  }

  throw new Error("Failed to submit feedback. Please try again.");
}

function derivePreferredLabels(choice: FeedbackChoice, assignments: BattleMetadata["assignments"]) {
  if (choice === "BOTH_GOOD") {
    return assignments.map((a) => a.label);
  }
  if (choice === "BOTH_BAD") {
    return [];
  }
  return [choice];
}

function getPageMarkdown(result: ProviderParseResult | undefined, pageNumber: number) {
  if (!result) return undefined;
  const page = result.pages.find((p) => p.page_number === pageNumber) ?? result.pages[0];
  return page?.markdown;
}
