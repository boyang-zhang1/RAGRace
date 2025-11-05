"use client";

import { useState } from "react";
import { FileUploadZone } from "@/components/parse/FileUploadZone";
import { ApiKeyForm } from "@/components/parse/ApiKeyForm";
import { PDFViewer } from "@/components/parse/PDFViewer";
import { MarkdownViewer } from "@/components/parse/MarkdownViewer";
import { CostDisplay } from "@/components/parse/CostDisplay";
import { ProcessingTimeDisplay } from "@/components/parse/ProcessingTimeDisplay";
import { PageNavigator } from "@/components/parse/PageNavigator";
import { ProviderLabel } from "@/components/providers/ProviderLabel";
import { Button } from "@/components/ui/button";
import { FileText, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { getProviderDisplayName } from "@/lib/providerMetadata";

interface PageData {
  page_number: number;
  markdown: string;
  images: string[];
  metadata: Record<string, any>;
}

interface ProviderResult {
  total_pages: number;
  pages: PageData[];
  processing_time: number;
  usage: Record<string, any>;
}

interface ParseResults {
  [provider: string]: ProviderResult;
}

interface CostData {
  provider: string;
  credits: number;
  usd_per_credit: number;
  total_usd: number;
  details: Record<string, any>;
}

interface CostResults {
  [provider: string]: CostData;
}

interface ApiKeys {
  llamaindex?: string;
  reducto?: string;
  landingai?: string;
}

export default function ParsePage() {
  const [apiKeys, setApiKeys] = useState<ApiKeys>({});
  const [hasApiKeys, setHasApiKeys] = useState(false);
  const [fileId, setFileId] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string>("");
  const [parseResults, setParseResults] = useState<ParseResults | null>(null);
  const [costResults, setCostResults] = useState<CostResults | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isParsing, setIsParsing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleKeysChange = (keys: ApiKeys, hasAtLeastOne: boolean) => {
    setApiKeys(keys);
    setHasApiKeys(hasAtLeastOne);
  };

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setError(null);

    try {
      const data = await apiClient.uploadPdf(file);
      setFileId(data.file_id);
      setFileName(data.filename);

      // Auto-trigger parse
      await handleParse(data.file_id);
    } catch (err) {
      console.error("Upload error:", err);
      setError(err instanceof Error ? err.message : "Failed to upload file");
    } finally {
      setIsUploading(false);
    }
  };

  const handleParse = async (fid: string) => {
    setIsParsing(true);
    setError(null);

    try {
      // Filter out empty keys and pass to API
      const validKeys: Record<string, string> = {};
      Object.entries(apiKeys).forEach(([provider, key]) => {
        if (key && key.trim()) {
          validKeys[provider] = key;
        }
      });

      const data = await apiClient.compareParses(fid, validKeys);
      setParseResults(data.results);

      // Set total pages from first available provider
      const firstProvider = Object.values(data.results)[0];
      setTotalPages(firstProvider?.total_pages || 0);
      setCurrentPage(1);

      // Calculate costs
      try {
        const costData = await apiClient.calculateParseCost(data);
        setCostResults(costData.costs);
      } catch (costErr) {
        console.error("Cost calculation error:", costErr);
        // Don't fail the entire parse if cost calculation fails
      }
    } catch (err) {
      console.error("Parse error:", err);
      setError(err instanceof Error ? err.message : "Failed to parse PDF");
    } finally {
      setIsParsing(false);
    }
  };

  const handleReset = () => {
    setFileId(null);
    setFileName("");
    setParseResults(null);
    setCostResults(null);
    setCurrentPage(1);
    setTotalPages(0);
    setError(null);
  };

  // Get markdown for a specific provider and page
  const getProviderMarkdown = (provider: string) => {
    if (!parseResults?.[provider]) return undefined;
    const page = parseResults[provider].pages.find(
      (p) => p.page_number === currentPage
    );
    return page?.markdown;
  };

  // Get list of providers that were run (have results)
  const runProviders = parseResults ? Object.keys(parseResults) : [];

  return (
    <div className="container mx-auto p-6 max-w-full px-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">PDF Parse & Compare</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Upload a PDF to compare parsing results from LlamaIndex, Reducto, and LandingAI
        </p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      {/* API Key Form - Always visible at top */}
      <div className="mb-6 max-w-2xl mx-auto">
        <ApiKeyForm onKeysChange={handleKeysChange} disabled={isUploading || isParsing} />
      </div>

      {!fileId ? (
        <div className="max-w-2xl mx-auto">
          <FileUploadZone onUpload={handleUpload} disabled={!hasApiKeys} />
          {!hasApiKeys && (
            <p className="mt-4 text-center text-sm text-gray-500">
              Please provide at least one API key above to enable upload
            </p>
          )}
          {isUploading && (
            <div className="mt-4 text-center text-gray-600 flex items-center justify-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Uploading...
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          {/* Header with file info and reset button */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-gray-500" />
              <span className="font-medium">{fileName}</span>
            </div>
            <Button variant="outline" onClick={handleReset}>
              Upload New File
            </Button>
          </div>

          {isParsing ? (
            <div className="text-center py-12">
              <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-blue-500" />
              <p className="text-lg font-medium">Parsing PDF...</p>
              <p className="text-sm text-gray-500 mt-2">
                This may take a few moments
              </p>
            </div>
          ) : parseResults ? (
            <>
              {/* PDF Viewer (Upper Section - Centered with Max Width) */}
              <div className="max-w-4xl mx-auto">
                <PDFViewer
                  fileId={fileId}
                  currentPage={currentPage}
                  onPageChange={setCurrentPage}
                  onLoadSuccess={(numPages) => {
                    if (totalPages === 0) {
                      setTotalPages(numPages);
                    }
                  }}
                />
              </div>

              {/* Page Navigator - Below PDF, Above Providers */}
              {totalPages > 0 && (
                <PageNavigator
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={setCurrentPage}
                />
              )}

              {/* Provider Comparison - Dynamic columns based on number of providers */}
              <div
                className={`grid gap-8 ${
                  runProviders.length === 1
                    ? "grid-cols-1 max-w-4xl mx-auto"
                    : runProviders.length === 2
                    ? "grid-cols-1 md:grid-cols-2"
                    : "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
                }`}
              >
                {runProviders.map((provider) => (
                  <div key={provider} className="space-y-4">
                    <MarkdownViewer
                      title={
                        <ProviderLabel
                          provider={provider}
                          size={26}
                          className="gap-2"
                        />
                      }
                      markdown={getProviderMarkdown(provider)}
                    />

                    {/* Info Cards Grid */}
                    <div className="grid grid-cols-2 gap-3">
                      {/* Processing Time Card */}
                      <ProcessingTimeDisplay
                        processingTime={parseResults[provider]?.processing_time || 0}
                        providerName={getProviderDisplayName(provider)}
                      />

                      {/* Cost Card */}
                      {costResults && costResults[provider] && (
                        <CostDisplay
                          cost={costResults[provider]}
                          providerName={getProviderDisplayName(provider)}
                        />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : null}
        </div>
      )}
    </div>
  );
}
