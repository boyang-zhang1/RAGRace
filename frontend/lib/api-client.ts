/**
 * API client for RAGRace backend
 */

import type {
  RunSummary,
  RunDetail,
  DatasetInfo,
  ResultsListResponse,
  BenchmarkRequest,
  BenchmarkResponse,
  DatasetPerformanceSummary,
  ProviderDetailResponse,
} from '@/types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async fetchWithError<T>(url: string, options?: RequestInit): Promise<T> {
    try {
      // Extract headers from options to avoid overwriting
      const { headers: optionHeaders, ...restOptions } = options || {};

      const response = await fetch(`${this.baseUrl}${url}`, {
        ...restOptions,
        headers: {
          'Content-Type': 'application/json',
          ...optionHeaders,
        },
      });

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

        try {
          const errorData = await response.json();

          // Handle FastAPI validation errors (422)
          if (errorData.detail) {
            if (Array.isArray(errorData.detail)) {
              // Pydantic validation errors: [{loc, msg, type}]
              errorMessage = errorData.detail
                .map((e: any) => `${e.loc.join('.')}: ${e.msg}`)
                .join('; ');
            } else {
              // String detail (403, 500, etc.)
              errorMessage = errorData.detail;
            }
          }
        } catch {
          // If JSON parsing fails, use status text
        }

        throw new Error(errorMessage);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unknown error occurred');
    }
  }

  /**
   * Get list of benchmark runs with pagination and filtering
   */
  async getResults(params?: {
    dataset?: string;
    limit?: number;
    offset?: number;
  }): Promise<ResultsListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.dataset) searchParams.append('dataset', params.dataset);
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());

    const query = searchParams.toString();
    const url = `/api/v1/results${query ? `?${query}` : ''}`;

    return this.fetchWithError<ResultsListResponse>(url);
  }

  /**
   * Get detailed results for a specific run
   */
  async getRunDetail(runId: string): Promise<RunDetail> {
    return this.fetchWithError<RunDetail>(`/api/v1/results/${runId}`);
  }

  /**
   * Get list of available datasets
   */
  async getDatasets(): Promise<DatasetInfo[]> {
    return this.fetchWithError<DatasetInfo[]>('/api/v1/datasets');
  }

  /**
   * Get all documents and Q&A results for a dataset across all runs
   *
   * @param datasetName Dataset identifier (e.g., 'qasper', 'squad2')
   * @returns Document-level breakdown with Q&A results (same structure as RunDetail)
   */
  async getDatasetDocuments(datasetName: string): Promise<RunDetail> {
    return this.fetchWithError<RunDetail>(
      `/api/v1/datasets/${encodeURIComponent(datasetName)}/documents`
    );
  }

  /**
   * Get aggregated provider performance for a dataset
   *
   * @param datasetName Dataset identifier (e.g., 'qasper', 'squad2')
   * @returns Performance summary with provider rankings
   */
  async getDatasetPerformance(datasetName: string): Promise<DatasetPerformanceSummary> {
    return this.fetchWithError<DatasetPerformanceSummary>(
      `/api/v1/datasets/${encodeURIComponent(datasetName)}/performance`
    );
  }

  /**
   * Get detailed document-level results for a provider on a dataset
   *
   * @param datasetName Dataset identifier
   * @param providerName Provider name
   * @returns Document-level breakdown for the provider
   */
  async getProviderDetail(
    datasetName: string,
    providerName: string
  ): Promise<ProviderDetailResponse> {
    return this.fetchWithError<ProviderDetailResponse>(
      `/api/v1/datasets/${encodeURIComponent(datasetName)}/providers/${encodeURIComponent(providerName)}`
    );
  }

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    return this.fetchWithError('/api/health');
  }

  /**
   * Create and execute a new benchmark run
   *
   * @param request Benchmark configuration (includes api_keys for providers)
   * @param apiKey Optional X-API-Key header for user authentication (deprecated - use api_keys in request instead)
   * @returns Benchmark response with run_id and status
   *
   * Note: This endpoint runs synchronously and may take 1-5+ minutes.
   * Use small values for max_docs/max_questions_per_doc for testing.
   */
  async createBenchmark(
    request: BenchmarkRequest,
    apiKey?: string
  ): Promise<BenchmarkResponse> {
    const headers: Record<string, string> = {};

    // Only include X-API-Key header if provided (for backward compatibility)
    if (apiKey && apiKey.trim()) {
      headers['X-API-Key'] = apiKey;
    }

    return this.fetchWithError<BenchmarkResponse>('/api/v1/benchmarks', {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Also export the class for testing
export default ApiClient;
