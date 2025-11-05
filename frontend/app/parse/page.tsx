"use client";

import { useState } from "react";
import { FileUploadZone } from "@/components/parse/FileUploadZone";
import { PDFViewer } from "@/components/parse/PDFViewer";
import { MarkdownViewer } from "@/components/parse/MarkdownViewer";
import { PageNavigator } from "@/components/parse/PageNavigator";
import { Button } from "@/components/ui/button";
import { FileText, Loader2 } from "lucide-react";

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
}

interface ParseResults {
  llamaindex?: ProviderResult;
  reducto?: ProviderResult;
  landingai?: ProviderResult;
}

export default function ParsePage() {
  const [fileId, setFileId] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string>("");
  const [parseResults, setParseResults] = useState<ParseResults | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isParsing, setIsParsing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${apiUrl}/api/v1/parse/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Upload failed");
      }

      const data = await response.json();
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
      const response = await fetch(`${apiUrl}/api/v1/parse/compare`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          file_id: fid,
          providers: ["llamaindex", "reducto", "landingai"],
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Parsing failed");
      }

      const data = await response.json();
      setParseResults(data.results);

      // Set total pages from first available provider
      const pages =
        data.results.llamaindex?.total_pages ||
        data.results.reducto?.total_pages ||
        data.results.landingai?.total_pages ||
        0;
      setTotalPages(pages);
      setCurrentPage(1);
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
    setCurrentPage(1);
    setTotalPages(0);
    setError(null);
  };

  const getLlamaIndexMarkdown = () => {
    if (!parseResults?.llamaindex) return undefined;
    const page = parseResults.llamaindex.pages.find(
      (p) => p.page_number === currentPage
    );
    return page?.markdown;
  };

  const getReductoMarkdown = () => {
    if (!parseResults?.reducto) return undefined;
    const page = parseResults.reducto.pages.find(
      (p) => p.page_number === currentPage
    );
    return page?.markdown;
  };

  const getLandingAIMarkdown = () => {
    if (!parseResults?.landingai) return undefined;
    const page = parseResults.landingai.pages.find(
      (p) => p.page_number === currentPage
    );
    return page?.markdown;
  };

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

      {!fileId ? (
        <div className="max-w-2xl mx-auto">
          <FileUploadZone onUpload={handleUpload} />
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

              {/* Provider Comparison (Lower Section - Three Columns with Responsive Stacking) */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                <MarkdownViewer
                  title="LlamaIndex"
                  markdown={getLlamaIndexMarkdown()}
                />
                <MarkdownViewer
                  title="Reducto"
                  markdown={getReductoMarkdown()}
                />
                <MarkdownViewer
                  title="LandingAI"
                  markdown={getLandingAIMarkdown()}
                />
              </div>

              {/* Processing Time Info */}
              <div className="text-sm text-gray-500 text-center">
                Processing times: LlamaIndex{" "}
                {parseResults.llamaindex?.processing_time.toFixed(2)}s |
                Reducto {parseResults.reducto?.processing_time.toFixed(2)}s |
                LandingAI {parseResults.landingai?.processing_time.toFixed(2)}s
              </div>
            </>
          ) : null}
        </div>
      )}
    </div>
  );
}
