"use client";

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
}: PDFViewerProps) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  // Use Adobe PDF parameters for page control and hide sidebar
  const pdfUrl = `${apiUrl}/api/v1/parse/file/${fileId}#page=${currentPage}&navpanes=0&toolbar=0`;

  return (
    <Card className="h-full">
      <CardHeader className="pb-4">
        <CardTitle className="text-2xl font-bold tracking-tight">Original PDF</CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="flex justify-center bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden">
          <iframe
            key={currentPage} // Force reload on page change
            src={pdfUrl}
            className="w-full h-[700px] border-0"
            title="PDF Viewer"
          />
        </div>
      </CardContent>
    </Card>
  );
}
