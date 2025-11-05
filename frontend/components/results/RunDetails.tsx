'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ProviderLabel } from '@/components/providers/ProviderLabel';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ChevronDown, ChevronRight } from 'lucide-react';
import type { DocumentResult, ProviderResult } from '@/types/api';

interface RunDetailsProps {
  documents: DocumentResult[];
  providers: string[];
}

export function RunDetails({ documents, providers }: RunDetailsProps) {
  return (
    <div className="space-y-6">
      {documents.map((doc) => (
        <DocumentCard key={doc.doc_id} document={doc} providers={providers} />
      ))}
    </div>
  );
}

function DocumentCard({ document, providers }: { document: DocumentResult; providers: string[] }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle>{document.doc_title}</CardTitle>
            <CardDescription className="mt-1">Document ID: {document.doc_id}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Provider Scores Table */}
        <div className="mb-4">
          <h4 className="text-sm font-medium mb-2">Provider Scores (Aggregated)</h4>
          <div className="rounded-md border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-2 text-left font-medium">Provider</th>
                  <th className="px-4 py-2 text-left font-medium">Status</th>
                  <th className="px-4 py-2 text-left font-medium">Duration</th>
                  <th className="px-4 py-2 text-left font-medium">Scores</th>
                </tr>
              </thead>
              <tbody>
                {providers.map((providerName) => {
                  const result = document.providers[providerName];
                  if (!result) return null;

                  return (
                    <tr key={providerName} className="border-b last:border-0">
                      <td className="px-4 py-2 font-medium">
                        <ProviderLabel provider={providerName} size={18} />
                      </td>
                      <td className="px-4 py-2">
                        <Badge variant={result.status === 'success' ? 'default' : 'destructive'}>
                          {result.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-2">
                        {result.duration_seconds ? `${result.duration_seconds.toFixed(2)}s` : 'N/A'}
                      </td>
                      <td className="px-4 py-2">
                        <ScoresDisplay scores={result.aggregated_scores} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Expandable Questions Section */}
        <Collapsible open={isOpen} onOpenChange={setIsOpen}>
          <CollapsibleTrigger className="flex items-center gap-2 text-sm font-medium hover:underline">
            {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            {isOpen ? 'Hide' : 'Show'} detailed question results
          </CollapsibleTrigger>
          <CollapsibleContent className="mt-4">
            <QuestionsView document={document} providers={providers} />
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  );
}

function QuestionsView({ document, providers }: { document: DocumentResult; providers: string[] }) {
  // Get all questions from the first provider that has results
  const firstProvider = providers.find((p) => document.providers[p]?.questions?.length > 0);
  if (!firstProvider || !document.providers[firstProvider]) {
    return <p className="text-sm text-muted-foreground">No questions available</p>;
  }

  const questions = document.providers[firstProvider].questions;

  return (
    <div className="space-y-4">
      {questions.map((question, idx) => (
        <Card key={question.question_id} className="border-l-4 border-l-primary">
          <CardHeader>
            <CardTitle className="text-base">Question {idx + 1}</CardTitle>
            <CardDescription className="text-sm mt-2">{question.question}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Ground Truth */}
            <div>
              <h5 className="text-sm font-medium mb-1">Ground Truth:</h5>
              <p className="text-sm text-muted-foreground bg-muted p-2 rounded">
                {question.ground_truth}
              </p>
            </div>

            {/* Provider Answers */}
            <div className="space-y-3">
              <h5 className="text-sm font-medium">Provider Answers:</h5>
              {providers.map((providerName) => {
                const providerResult = document.providers[providerName];
                const answer = providerResult?.questions?.find(
                  (q) => q.question_id === question.question_id
                );

                if (!answer) return null;

                return (
                  <div key={providerName} className="border rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <Badge variant="outline" className="gap-1.5">
                        <ProviderLabel
                          provider={providerName}
                          size={14}
                          nameClassName="text-xs font-semibold"
                        />
                      </Badge>
                      <div className="flex gap-2">
                        {answer.response_latency_ms && (
                          <span className="text-xs text-muted-foreground">
                            {answer.response_latency_ms.toFixed(0)}ms
                          </span>
                        )}
                        <ScoresDisplay scores={answer.evaluation_scores} />
                      </div>
                    </div>
                    <p className="text-sm mb-2">{answer.response_answer}</p>
                    {answer.response_context && answer.response_context.length > 0 && (
                      <details className="text-xs text-muted-foreground mt-2">
                        <summary className="cursor-pointer hover:underline">
                          Retrieved context ({answer.response_context.length} chunks)
                        </summary>
                        <div className="mt-2 space-y-1 pl-4">
                          {answer.response_context.map((ctx, i) => (
                            <div key={i} className="border-l-2 border-muted pl-2">
                              {ctx}
                            </div>
                          ))}
                        </div>
                      </details>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function ScoresDisplay({ scores }: { scores: Record<string, any> }) {
  const entries = Object.entries(scores);

  if (entries.length === 0) {
    return <span className="text-xs text-muted-foreground">No scores</span>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {entries.map(([metric, value]) => (
        <span key={metric} className="text-xs bg-muted px-2 py-0.5 rounded">
          {metric}: {typeof value === 'number' ? value.toFixed(3) : value}
        </span>
      ))}
    </div>
  );
}
