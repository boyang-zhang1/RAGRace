import { Suspense } from 'react';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { format } from 'date-fns';
import { apiClient } from '@/lib/api-client';
import { RunDetails } from '@/components/results/RunDetails';
import { OverallResultsCard } from '@/components/results/OverallResultsCard';
import { Badge } from '@/components/ui/badge';
import { ProviderLabel } from '@/components/providers/ProviderLabel';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft } from 'lucide-react';
import { ContactIcons } from '@/components/ui/ContactIcons';

interface PageProps {
  params: Promise<{ run_id: string }>;
}

function getStatusBadgeVariant(status: string) {
  switch (status) {
    case 'completed':
      return 'default';
    case 'running':
      return 'secondary';
    case 'failed':
      return 'destructive';
    default:
      return 'outline';
  }
}

async function RunDetailContent({ runId }: { runId: string }) {
  let run: Awaited<ReturnType<typeof apiClient.getRunDetail>> | null = null;
  let fetchError: unknown = null;

  try {
    run = await apiClient.getRunDetail(runId);
  } catch (error) {
    if (error instanceof Error && error.message.includes('404')) {
      notFound();
    }
    fetchError = error;
  }

  if (!run) {
    const message = fetchError instanceof Error ? fetchError.message : 'Failed to load run details';

    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-destructive mb-2">Error Loading Run Details</h2>
        <p className="text-muted-foreground">{message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
        {/* Back Link */}
        <Link
          href="/datasets"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-primary"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Datasets
        </Link>

        {/* Run Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{run.run_id}</h1>
          <p className="text-muted-foreground mt-2">Detailed benchmark run results</p>
        </div>

        {/* Run Metadata Card */}
        <Card>
          <CardContent className="pt-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Dataset</p>
                <p className="text-lg font-semibold mt-1">
                  {run.dataset}
                  <span className="text-sm text-muted-foreground ml-2">({run.split})</span>
                </p>
              </div>

              <div>
                <p className="text-sm font-medium text-muted-foreground">Status</p>
                <div className="mt-1">
                  <Badge variant={getStatusBadgeVariant(run.status)}>{run.status}</Badge>
                </div>
              </div>

              <div>
                <p className="text-sm font-medium text-muted-foreground">Documents</p>
                <p className="text-lg font-semibold mt-1">{run.num_docs}</p>
              </div>

              <div>
                <p className="text-sm font-medium text-muted-foreground">Questions</p>
                <p className="text-lg font-semibold mt-1">{run.num_questions}</p>
              </div>

              <div>
                <p className="text-sm font-medium text-muted-foreground">Started</p>
                <p className="text-sm mt-1">
                  {run.started_at ? format(new Date(run.started_at), 'PPpp') : 'N/A'}
                </p>
              </div>

              <div>
                <p className="text-sm font-medium text-muted-foreground">Duration</p>
                <p className="text-sm mt-1">
                  {run.duration_seconds
                    ? `${(run.duration_seconds / 60).toFixed(2)} minutes`
                    : 'N/A'}
                </p>
              </div>

              <div className="col-span-2">
                <p className="text-sm font-medium text-muted-foreground">Providers</p>
                <div className="flex flex-wrap gap-2 mt-1">
                  {run.providers.map((provider) => (
                    <Badge key={provider} variant="outline" className="gap-1.5">
                      <ProviderLabel
                        provider={provider}
                        size={16}
                        nameClassName="text-xs font-semibold"
                      />
                    </Badge>
                  ))}
                </div>
              </div>
            </div>

            {run.error_message && (
              <div className="mt-6 p-4 bg-destructive/10 border border-destructive rounded-lg">
                <p className="text-sm font-medium text-destructive">Error:</p>
                <p className="text-sm text-destructive/80 mt-1">{run.error_message}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Overall Results */}
        {run.documents.length > 0 && (
          <OverallResultsCard documents={run.documents} providers={run.providers} />
        )}

        {/* Document Results */}
        <div>
          <h2 className="text-2xl font-bold mb-4">Document Results</h2>
          <RunDetails documents={run.documents} providers={run.providers} />
        </div>
      </div>
  );
}

function RunDetailLoading() {
  return (
    <div className="space-y-6">
      {/* Back Link Skeleton */}
      <Skeleton className="h-8 w-32" />

      {/* Loading Message - Prominent */}
      <div className="text-center py-12">
        <div className="inline-flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <div>
            <h2 className="text-2xl font-bold mb-2">Loading Results</h2>
            <p className="text-muted-foreground">
              Fetching benchmark data from database...
            </p>
          </div>
        </div>
      </div>

      {/* Skeleton Content */}
      <div className="space-y-2">
        <Skeleton className="h-10 w-96" />
        <Skeleton className="h-5 w-64" />
      </div>
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i}>
                <Skeleton className="h-4 w-24 mb-2" />
                <Skeleton className="h-6 w-32" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      <div className="space-y-4">
        {[...Array(2)].map((_, i) => (
          <Skeleton key={i} className="h-64 w-full" />
        ))}
      </div>
    </div>
  );
}

export default async function RunDetailPage({ params }: PageProps) {
  const { run_id } = await params;

  return (
    <>
      <Suspense fallback={<RunDetailLoading />}>
        <RunDetailContent runId={run_id} />
      </Suspense>
      <ContactIcons />
    </>
  );
}
