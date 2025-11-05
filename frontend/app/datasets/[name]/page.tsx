import { Suspense } from 'react';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import { RunDetails } from '@/components/results/RunDetails';
import { OverallResultsCard } from '@/components/results/OverallResultsCard';
import { Badge } from '@/components/ui/badge';
import { ProviderLabel } from '@/components/providers/ProviderLabel';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft } from 'lucide-react';

interface PageProps {
  params: Promise<{ name: string }>;
}

async function DatasetDetailContent({ datasetName }: { datasetName: string }) {
  let data: Awaited<ReturnType<typeof apiClient.getDatasetDocuments>> | null = null;
  let displayName = datasetName.toUpperCase();
  let fetchError: unknown = null;

  try {
    data = await apiClient.getDatasetDocuments(datasetName);
    const datasets = await apiClient.getDatasets();
    const datasetInfo = datasets.find((d) => d.name === datasetName);
    if (datasetInfo?.display_name) {
      displayName = datasetInfo.display_name;
    }
  } catch (error) {
    if (error instanceof Error && error.message.includes('404')) {
      notFound();
    }
    fetchError = error;
  }

  if (!data) {
    const message = fetchError instanceof Error ? fetchError.message : 'Failed to load dataset details';

    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-destructive mb-2">Error Loading Dataset Details</h2>
        <p className="text-muted-foreground">{message}</p>
        <Link
          href="/datasets"
          className="inline-flex items-center text-sm text-primary hover:underline mt-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Datasets
        </Link>
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

      {/* Dataset Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{displayName}</h1>
        <p className="text-muted-foreground mt-2">
          Aggregated results across all benchmark runs
        </p>
      </div>

      {/* Dataset Metadata Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Dataset</p>
              <p className="text-lg font-semibold mt-1">{datasetName}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground">Aggregation Scope</p>
              <div className="mt-1">
                <Badge variant="outline">All Splits</Badge>
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground">Documents</p>
              <p className="text-lg font-semibold mt-1">{data.num_docs}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground">Questions</p>
              <p className="text-lg font-semibold mt-1">{data.num_questions}</p>
            </div>

            <div className="col-span-2">
              <p className="text-sm font-medium text-muted-foreground">Providers Tested</p>
              <div className="flex flex-wrap gap-2 mt-1">
                {data.providers.map((provider) => (
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
        </CardContent>
      </Card>

      {/* Overall Results */}
      {data.documents.length > 0 && (
        <OverallResultsCard documents={data.documents} providers={data.providers} />
      )}

      {/* Document Results */}
      <div>
        <h2 className="text-2xl font-bold mb-4">Document Results</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Showing latest successful results for each provider per document
        </p>
        <RunDetails documents={data.documents} providers={data.providers} />
      </div>
    </div>
  );
}

function DatasetDetailLoading() {
  return (
    <div className="space-y-6">
      {/* Back Link Skeleton */}
      <Skeleton className="h-8 w-32" />

      {/* Loading Message - Prominent */}
      <div className="text-center py-12">
        <div className="inline-flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <div>
            <h2 className="text-2xl font-bold mb-2">Loading Dataset Results</h2>
            <p className="text-muted-foreground">
              Aggregating benchmark data across all runs...
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

export default async function DatasetDetailPage({ params }: PageProps) {
  const { name } = await params;

  return (
    <Suspense fallback={<DatasetDetailLoading />}>
      <DatasetDetailContent datasetName={name} />
    </Suspense>
  );
}
