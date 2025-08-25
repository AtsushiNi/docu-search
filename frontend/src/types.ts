export interface SearchResult {
  _id: string;
  _source: {
    title: string;
    name: string;
    content: string;
    url: string;
    updated_at: string;
  };
  highlight?: {
    content: string[];
  };
}

export interface RQJob {
  id: string;
  queue: string;
  status: string;
  created_at: string | null;
  started_at: string | null;
  ended_at: string | null;
  result: string | null;
  exc_info: string | null;
  function: string;
  args: unknown[];
  kwargs: Record<string, unknown>;
  error?: string;
}

export interface QueueStats {
  [queueName: string]: {
    count: number;
    failed_jobs: number;
    scheduled_jobs: number;
  };
}
