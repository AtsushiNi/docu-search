import React from 'react';

export interface SearchResult {
  _id: string;
  _source: {
    name: string;
    content: string;
    url: string;
    updated_at: string;
    pdf_name?: string;
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
  first_arg: unknown;
  kwargs: Record<string, unknown>;
  error?: string;
}

export interface QueueStats {
  [queueName: string]: {
    queued_jobs: number;
    started_jobs: number;
    successful_jobs: number;
    failed_jobs: number;
  };
}

export interface FileItem {
  id: string;
  url: string;
  filename?: string;
  is_directory?: boolean;
}

export interface TreeNode {
  key: string;
  title: string | React.ReactNode;
  isLeaf: boolean;
  children?: TreeNode[];
  url?: string;
  id?: string;
}
