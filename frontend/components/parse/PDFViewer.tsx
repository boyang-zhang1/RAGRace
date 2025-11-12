"use client";

import { useEffect, useState, useRef } from "react";
import { PDFDocument } from "pdf-lib";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface PDFViewerProps {
  fileId: string;
  currentPage: number;
  onPageChange: (page: number) => void;
  onLoadSuccess?: (numPages: number) => void;
}

export function PDFViewer({
  fileId,
  currentPage,
  onLoadSuccess,
}: PDFViewerProps) {
  const [pdfDoc, setPdfDoc] = useState<PDFDocument | null>(null);
  const [pageUrl, setPageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const previousUrlRef = useRef<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Load full PDF once when fileId changes
  useEffect(() => {
    let mounted = true;

    async function loadPdf() {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`${apiUrl}/api/v1/parse/file/${fileId}`);
        if (!response.ok) {
          throw new Error(`Failed to load PDF: ${response.statusText}`);
        }

        const pdfBytes = await response.arrayBuffer();
        const loadedPdf = await PDFDocument.load(pdfBytes);

        if (mounted) {
          setPdfDoc(loadedPdf);
          const numPages = loadedPdf.getPageCount();
          onLoadSuccess?.(numPages);
          setLoading(false);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load PDF");
          setLoading(false);
        }
      }
    }

    loadPdf();

    return () => {
      mounted = false;
    };
  }, [fileId, apiUrl, onLoadSuccess]);

  // Extract current page when page changes
  useEffect(() => {
    if (!pdfDoc) return;

    let mounted = true;

    async function extractPage() {
      if (!pdfDoc) return; // Additional null check for TypeScript

      try {
        // Create new PDF with only current page
        const singlePagePdf = await PDFDocument.create();
        const pageIndex = currentPage - 1; // Convert to 0-indexed

        if (pageIndex < 0 || pageIndex >= pdfDoc.getPageCount()) {
          throw new Error(`Page ${currentPage} is out of range`);
        }

        const [copiedPage] = await singlePagePdf.copyPages(pdfDoc, [pageIndex]);
        singlePagePdf.addPage(copiedPage);

        const pdfBytes = await singlePagePdf.save();
        const blob = new Blob([new Uint8Array(pdfBytes)], { type: "application/pdf" });
        const blobUrl = URL.createObjectURL(blob);
        // Add Adobe PDF parameters to hide navigation panes and toolbar
        const url = `${blobUrl}#navpanes=0&toolbar=0`;

        if (mounted) {
          // Revoke old URL to prevent memory leak
          if (previousUrlRef.current) {
            // Extract the base blob URL before revoking (without parameters)
            const baseBlobUrl = previousUrlRef.current.split('#')[0];
            URL.revokeObjectURL(baseBlobUrl);
          }
          previousUrlRef.current = url;
          setPageUrl(url);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to extract page");
        }
      }
    }

    extractPage();

    return () => {
      mounted = false;
    };
  }, [pdfDoc, currentPage]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (previousUrlRef.current) {
        // Extract the base blob URL before revoking (without parameters)
        const baseBlobUrl = previousUrlRef.current.split('#')[0];
        URL.revokeObjectURL(baseBlobUrl);
      }
    };
  }, []);

  return (
    <Card className="h-full">
      <CardHeader className="pb-4">
        <CardTitle className="text-2xl font-bold tracking-tight">Original PDF</CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="flex justify-center bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden">
          {loading && (
            <div className="w-full h-[700px] flex items-center justify-center">
              <p className="text-gray-500">Loading PDF...</p>
            </div>
          )}
          {error && (
            <div className="w-full h-[700px] flex items-center justify-center">
              <p className="text-red-500">{error}</p>
            </div>
          )}
          {!loading && !error && pageUrl && (
            <iframe
              src={pageUrl}
              className="w-full h-[700px] border-0"
              title="PDF Viewer"
            />
          )}
        </div>
      </CardContent>
    </Card>
  );
}
