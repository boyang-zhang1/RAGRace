/**
 * TypeScript types matching the FastAPI backend response models
 * Based on backend/api/models/responses.py
 */

export interface RunSummary {
  run_id: string;
  dataset: string;
  split: string;
  providers: string[];
  status: 'queued' | 'running' | 'completed' | 'failed';
  num_docs: number;
  num_questions: number;
  started_at: string;  // ISO datetime string
  completed_at: string | null;
  duration_seconds: number | null;
}

export interface QuestionResult {
  question_id: string;
  question: string;
  ground_truth: string;
  response_answer: string;
  response_context: string[];  // Retrieved text chunks
  response_latency_ms: number | null;
  evaluation_scores: Record<string, any>;  // {metric: score}
}

export interface ProviderResult {
  provider: string;
  status: 'success' | 'error';
  error: string | null;
  aggregated_scores: Record<string, any>;  // {metric: avg_score}
  duration_seconds: number | null;
  questions: QuestionResult[];
}

export interface DocumentResult {
  doc_id: string;
  doc_title: string;
  providers: Record<string, ProviderResult>;  // provider_name -> result
}

export interface RunDetail {
  run_id: string;
  dataset: string;
  split: string;
  providers: string[];
  status: 'queued' | 'running' | 'completed' | 'failed';
  num_docs: number;
  num_questions: number;
  config: Record<string, any>;  // Full benchmark config
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  error_message: string | null;
  documents: DocumentResult[];
}

export interface DatasetInfo {
  name: string;
  display_name: string;
  description: string;
  available_splits: string[];
  num_documents: number | null;
  task_type: string;
}

export interface ResultsListResponse {
  runs: RunSummary[];
  total: number;
  limit: number;
  offset: number;
}

// API Error Response
export interface ApiError {
  detail: string;
}

// Benchmark Creation Request
export interface BenchmarkRequest {
  dataset: string;
  split: string;
  providers: string[];
  max_docs: number | null;
  max_questions_per_doc: number | null;
  filter_unanswerable: boolean;
  api_keys?: Record<string, string>;  // Optional: provider API keys (openai, llamaindex, landingai, reducto)
}

// Benchmark Creation Response
export interface BenchmarkResponse {
  run_id: string;
  status: string;
  message: string;
  duration_seconds: number | null;
}

// Dataset Performance Types
export interface ProviderPerformance {
  provider: string;
  num_documents: number;
  num_runs: number;
  aggregated_scores: Record<string, number>;  // {metric: avg_score}
  avg_duration_seconds: number | null;
}

export interface DatasetPerformanceSummary {
  dataset_name: string;
  total_runs: number;
  total_documents: number;
  providers: ProviderPerformance[];
  last_run_date: string | null;  // ISO datetime string
}

export interface ProviderDocumentDetail {
  doc_id: string;
  doc_title: string;
  run_id: string;
  run_date: string;  // ISO datetime string
  aggregated_scores: Record<string, any>;
  duration_seconds: number | null;
  status: 'success' | 'error';
}

export interface ProviderDetailResponse {
  dataset_name: string;
  provider: string;
  total_documents: number;
  total_runs: number;
  overall_scores: Record<string, number>;
  documents: ProviderDocumentDetail[];
}
