import { notFound } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowLeft, FileText } from 'lucide-react';
import type { ProviderDetailResponse } from '@/types/api';

interface PageProps {
  params: Promise<{
    name: string;
    provider: string;
  }>;
}

export default async function ProviderDetailPage({ params }: PageProps) {
  const { name, provider } = await params;

  let details: ProviderDetailResponse | null = null;
  let fetchError: unknown = null;

  try {
    details = await apiClient.getProviderDetail(name, provider);
  } catch (error) {
    if (error instanceof Error && error.message.includes('404')) {
      notFound();
    }
    fetchError = error;
  }

  if (!details) {
    const message = fetchError instanceof Error ? fetchError.message : 'Failed to load provider details';

    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-destructive mb-2">Error Loading Results</h2>
        <p className="text-muted-foreground">{message}</p>
        <Link href="/datasets">
          <Button variant="outline" className="mt-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Datasets
          </Button>
        </Link>
      </div>
    );
  }

  // Extract all metric names
  const metricNames = Array.from(
    new Set(
      details.documents.flatMap((doc) => Object.keys(doc.aggregated_scores))
    )
  ).sort();

  return (
    <div>
      {/* Header with back button */}
      <div className="mb-6">
        <Link href="/datasets">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Datasets
          </Button>
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              {details.provider} on {details.dataset_name.toUpperCase()}
            </h1>
            <p className="text-muted-foreground mt-2">
              Document-level performance breakdown
            </p>
          </div>
        </div>
      </div>

      {/* Overall Stats */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Overall Performance</CardTitle>
          <CardDescription>
            Aggregated across {details.total_documents} documents from {details.total_runs} runs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(details.overall_scores).map(([metric, score]) => (
              <div key={metric}>
                <p className="text-sm text-muted-foreground">{formatMetricName(metric)}</p>
                <p className="text-2xl font-bold mt-1">{score.toFixed(3)}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Document-level Results Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            <CardTitle>Document-Level Results</CardTitle>
          </div>
          <CardDescription>
            Performance for each document (latest run only)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-3 py-2 text-left font-medium sticky left-0 bg-muted/50">
                    Document
                  </th>
                  <th className="px-3 py-2 text-left font-medium">Run ID</th>
                  <th className="px-3 py-2 text-left font-medium">Date</th>
                  <th className="px-3 py-2 text-left font-medium">Status</th>
                  <th className="px-3 py-2 text-left font-medium">Duration</th>
                  {metricNames.map((metric) => (
                    <th key={metric} className="px-3 py-2 text-left font-medium whitespace-nowrap">
                      {formatMetricName(metric)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {details.documents.map((doc) => (
                  <tr key={doc.doc_id} className="border-b last:border-0 hover:bg-muted/50">
                    <td className="px-3 py-2 sticky left-0 bg-background">
                      <div className="max-w-[200px]">
                        <p className="font-medium truncate" title={doc.doc_title}>
                          {doc.doc_title}
                        </p>
                        <p className="text-xs text-muted-foreground">{doc.doc_id}</p>
                      </div>
                    </td>
                    <td className="px-3 py-2">
                      <Link href={`/results/${doc.run_id}`}>
                        <Badge variant="outline" className="cursor-pointer hover:bg-muted">
                          {doc.run_id.replace('run_', '')}
                        </Badge>
                      </Link>
                    </td>
                    <td className="px-3 py-2 text-muted-foreground">
                      {new Date(doc.run_date).toLocaleDateString()}
                    </td>
                    <td className="px-3 py-2">
                      <Badge variant={doc.status === 'success' ? 'default' : 'destructive'}>
                        {doc.status}
                      </Badge>
                    </td>
                    <td className="px-3 py-2 text-muted-foreground tabular-nums">
                      {doc.duration_seconds ? `${doc.duration_seconds.toFixed(2)}s` : '-'}
                    </td>
                    {metricNames.map((metric) => (
                      <td key={metric} className="px-3 py-2 text-muted-foreground tabular-nums">
                        {formatScore(doc.aggregated_scores[metric])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Format metric name for display
 */
function formatMetricName(metric: string): string {
  // Remove (mode=f1) suffix for brevity
  const cleaned = metric.replace(/\(mode=[^)]+\)/g, '');

  // Convert snake_case to Title Case
  return cleaned
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Format score for display
 */
function formatScore(score: number | undefined): string {
  if (score === undefined || score === null) return '-';
  return score.toFixed(3);
}
