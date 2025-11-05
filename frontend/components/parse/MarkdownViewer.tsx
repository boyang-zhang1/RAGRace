"use client";

import type { ReactNode } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface MarkdownViewerProps {
  title: ReactNode;
  markdown: string | undefined;
  isLoading?: boolean;
}

export function MarkdownViewer({
  title,
  markdown,
  isLoading = false,
}: MarkdownViewerProps) {
  const markdownComponents: Components = {
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
          className="min-w-full border-collapse border border-gray-400"
          {...props}
        />
      </div>
    ),
    thead: ({ node, ...props }) => (
      <thead className="bg-gray-100 dark:bg-gray-800" {...props} />
    ),
    tbody: ({ node, ...props }) => (
      <tbody className="divide-y divide-gray-300" {...props} />
    ),
    tr: ({ node, ...props }) => (
      <tr className="border-b border-gray-300" {...props} />
    ),
    th: ({ node, ...props }) => (
      <th
        className="border border-gray-400 px-4 py-2 text-left font-semibold bg-gray-100 dark:bg-gray-800"
        {...props}
      />
    ),
    td: ({ node, ...props }) => (
      <td
        className="border border-gray-300 px-4 py-2"
        {...props}
      />
    ),
    // Custom code block styling
    code: ({ inline, ...props }: { inline?: boolean } & React.HTMLAttributes<HTMLElement>) =>
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
  };

  return (
    <Card className="h-full">
      <CardHeader className="pb-4">
        <CardTitle className="text-2xl font-bold tracking-tight">{title}</CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        {isLoading ? (
          <div className="text-center text-gray-500 p-4">
            Parsing with {title}...
          </div>
        ) : markdown ? (
          <div className="prose dark:prose-invert max-w-none prose-lg prose-headings:font-bold prose-h1:text-3xl prose-h2:text-2xl prose-h3:text-xl text-[17px] leading-relaxed">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw]}
              components={markdownComponents}
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
