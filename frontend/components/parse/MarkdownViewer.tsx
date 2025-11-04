"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface MarkdownViewerProps {
  title: string;
  markdown: string | undefined;
  isLoading?: boolean;
}

export function MarkdownViewer({
  title,
  markdown,
  isLoading = false,
}: MarkdownViewerProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="text-center text-gray-500 p-4">
            Parsing with {title}...
          </div>
        ) : markdown ? (
          <div className="prose dark:prose-invert max-w-none prose-sm prose-headings:font-bold prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw]}
              components={{
                // Custom heading styling
                h1: ({ node, ...props }) => (
                  <h1 className="text-2xl font-bold mt-6 mb-4" {...props} />
                ),
                h2: ({ node, ...props }) => (
                  <h2 className="text-xl font-bold mt-5 mb-3" {...props} />
                ),
                h3: ({ node, ...props }) => (
                  <h3 className="text-lg font-bold mt-4 mb-2" {...props} />
                ),
                // Custom table styling
                table: ({ node, ...props }) => (
                  <div className="overflow-x-auto my-4">
                    <table
                      className="min-w-full divide-y divide-gray-300 border"
                      {...props}
                    />
                  </div>
                ),
                // Custom code block styling
                code: ({ node, inline, ...props }) =>
                  inline ? (
                    <code
                      className="px-1 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-sm"
                      {...props}
                    />
                  ) : (
                    <code
                      className="block p-2 bg-gray-100 dark:bg-gray-800 rounded text-sm overflow-x-auto"
                      {...props}
                    />
                  ),
              }}
            >
              {markdown}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="text-center text-gray-400 p-4 italic">
            No content for this page
          </div>
        )}
      </CardContent>
    </Card>
  );
}
