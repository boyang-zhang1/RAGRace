"use client";

import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeRaw from "rehype-raw";
import rehypeKatex from "rehype-katex";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import "katex/dist/katex.min.css";

// Helper to generate unique IDs for mermaid diagrams
const generateId = () => `mermaid-${Math.random().toString(36).substr(2, 9)}`;

// Component to render Mermaid diagrams client-side
function MermaidRenderer({ code }: { code: string }) {
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string>("");
  const id = useRef(generateId());

  useEffect(() => {
    const renderDiagram = async () => {
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          theme: "default",
          securityLevel: "loose",
        });

        const { svg } = await mermaid.render(id.current, code);
        setSvg(svg);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      }
    };

    renderDiagram();
  }, [code]);

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded p-4 text-red-800 dark:text-red-300">
        <strong>Mermaid Error:</strong> {error}
      </div>
    );
  }

  if (!svg) {
    return <div className="text-gray-400 p-4">Rendering diagram...</div>;
  }

  return <div dangerouslySetInnerHTML={{ __html: svg }} />;
}

interface MarkdownViewerProps {
  title: ReactNode;
  markdown: string | undefined;
  isLoading?: boolean;
  subtitle?: ReactNode;
  footer?: ReactNode;
  cardClassName?: string;
}

export function MarkdownViewer({
  title,
  markdown,
  isLoading = false,
  subtitle,
  footer,
  cardClassName,
}: MarkdownViewerProps) {
  // Preprocess markdown to normalize LaTeX syntax
  // Convert \( ... \) to $ ... $ and \[ ... \] to $$ ... $$
  const processedMarkdown = markdown
    ? markdown
        .replace(/\\\((.*?)\\\)/g, (_, content) => `$${content}$`)  // Inline: \(...\) -> $...$
        .replace(/\\\[(.*?)\\\]/gs, (_, content) => `$$\n${content}\n$$`)  // Display: \[...\] -> $$...$$
    : undefined;

  const markdownComponents: Components = {
    // Custom pre styling - remove frame for mermaid diagrams
    pre: ({ node, children, ...props }) => {
      // Check if this pre contains a mermaid code block
      const child = children as any;
      const isMermaid = child?.props?.className?.includes('language-mermaid');

      if (isMermaid) {
        // No frame for mermaid - just render children
        return <div className="my-4">{children}</div>;
      }

      // Default pre styling for other code blocks
      return (
        <pre className="bg-gray-100 dark:bg-gray-800 rounded p-4 overflow-x-auto" {...props}>
          {children}
        </pre>
      );
    },
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
    code: ({ inline, className, children, ...props }: { inline?: boolean; className?: string } & React.HTMLAttributes<HTMLElement>) => {
      // Detect mermaid code blocks
      const match = /language-(\w+)/.exec(className || "");
      const language = match?.[1];
      const code = String(children).replace(/\n$/, "");

      // Render mermaid diagrams with custom component
      if (!inline && language === "mermaid") {
        return <MermaidRenderer code={code} />;
      }

      // Regular code rendering
      return inline ? (
        <code
          className="px-1 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-sm"
          {...props}
        >
          {children}
        </code>
      ) : (
        <code
          className="block p-2 bg-gray-100 dark:bg-gray-800 rounded text-sm overflow-x-auto"
          {...props}
        >
          {children}
        </code>
      );
    },
  };

  return (
    <Card className={cn("h-full flex flex-col", cardClassName)}>
      <CardHeader className="pb-4">
        <CardTitle className="text-2xl font-bold tracking-tight">{title}</CardTitle>
        {subtitle && (
          <p className="text-sm text-gray-500 dark:text-gray-400">{subtitle}</p>
        )}
      </CardHeader>
      <CardContent className="p-6 flex-1 flex flex-col">
        {isLoading ? (
          <div className="text-center text-gray-500 p-4">
            Parsing with {title}...
          </div>
        ) : markdown ? (
          <div className="flex-1 flex flex-col">
            <div className="prose dark:prose-invert max-w-none prose-lg prose-headings:font-bold prose-h1:text-3xl prose-h2:text-2xl prose-h3:text-xl text-[17px] leading-relaxed">
              <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex, rehypeRaw]}
                components={markdownComponents}
              >
                {processedMarkdown}
              </ReactMarkdown>
            </div>
            <details className="mt-4 rounded-md border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/30 p-4 text-sm text-gray-600 dark:text-gray-300">
              <summary className="cursor-pointer font-medium">
                Original Markdown / HTML
              </summary>
              <pre className="mt-3 whitespace-pre-wrap break-words text-xs text-gray-800 dark:text-gray-100 bg-transparent">
                {markdown}
              </pre>
            </details>
          </div>
        ) : (
          <div className="text-center text-gray-400 p-4 italic">
            No content for this page
          </div>
        )}

        {footer && (
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-800">
            {footer}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
