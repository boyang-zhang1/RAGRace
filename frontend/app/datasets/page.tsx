import { apiClient } from '@/lib/api-client';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DatasetPerformanceCard } from '@/components/datasets/DatasetPerformanceCard';

export default async function DatasetsPage() {
  try {
    const datasets = await apiClient.getDatasets();

    // Fetch performance data for each dataset in parallel
    const performancePromises = datasets.map(async (dataset) => {
      try {
        const performance = await apiClient.getDatasetPerformance(dataset.name);
        return { dataset, performance };
      } catch (error) {
        // If no performance data available, return null
        console.error(`No performance data for ${dataset.name}:`, error);
        return { dataset, performance: null };
      }
    });

    const datasetResults = await Promise.all(performancePromises);

    return (
      <div>
        <div className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight">Datasets & Performance</h1>
          <p className="text-muted-foreground mt-2">
            Benchmark results aggregated across all runs for each dataset
          </p>
        </div>

        <div className="space-y-8">
          {datasetResults.map(({ dataset, performance }) => (
            <Link key={dataset.name} href={`/datasets/${dataset.name}`}>
              <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
                {/* Dataset Header */}
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-2xl hover:text-primary transition-colors">
                        {dataset.display_name}
                      </CardTitle>
                      <CardDescription className="mt-1">{dataset.description}</CardDescription>
                    </div>
                    <Badge variant="outline" className="ml-4">
                      {dataset.task_type}
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent>
                  {/* Dataset Metadata */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-6">
                    <div>
                      <p className="text-muted-foreground">Available Splits</p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {dataset.available_splits.map((split) => (
                          <Badge key={split} variant="secondary" className="text-xs">
                            {split}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    {dataset.num_documents && (
                      <div>
                        <p className="text-muted-foreground">Total Documents</p>
                        <p className="text-xl font-bold mt-1">
                          {dataset.num_documents.toLocaleString()}
                        </p>
                      </div>
                    )}
                    {performance && (
                      <>
                        <div>
                          <p className="text-muted-foreground">Benchmark Runs</p>
                          <p className="text-xl font-bold mt-1">{performance.total_runs}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Providers Tested</p>
                          <p className="text-xl font-bold mt-1">{performance.providers.length}</p>
                        </div>
                      </>
                    )}
                  </div>

                  {/* Performance Results */}
                  {performance && performance.providers.length > 0 ? (
                    <div className="border-t pt-6">
                      <DatasetPerformanceCard
                        datasetName={dataset.name}
                        providers={performance.providers}
                        totalDocuments={performance.total_documents}
                        totalRuns={performance.total_runs}
                        embedded={true}
                      />
                    </div>
                  ) : (
                    <div className="py-8 text-center text-muted-foreground border-t">
                      No benchmark results available for this dataset yet.
                    </div>
                  )}
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    );
  } catch (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-destructive mb-2">Error Loading Datasets</h2>
        <p className="text-muted-foreground">
          {error instanceof Error ? error.message : 'Failed to load datasets'}
        </p>
      </div>
    );
  }
}
