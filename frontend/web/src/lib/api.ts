const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    throw new ApiError(401, 'Unauthorized');
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new ApiError(res.status, body.detail || 'Request failed');
  }

  return res.json();
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  role: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// --- Paginated response wrapper ---

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// --- Knowledge Base ---

export interface KBArticleListItem {
  id: string;
  title: string;
  source_type: string | null;
  status: string;
  category: string | null;
  module: string | null;
  created_at: string;
  body_preview: string;
}

export interface LineageEntry {
  source_id: string | null;
  relationship: string | null;
  evidence_snippet: string | null;
}

export interface KBArticleDetail {
  id: string;
  title: string;
  body: string;
  source_type: string | null;
  status: string;
  category: string | null;
  module: string | null;
  tags: string | null;
  created_at: string;
  updated_at: string;
  lineage: LineageEntry[];
}

// --- Learning Feed ---

export interface LearningEvent {
  id: string;
  trigger_ticket_id: string | null;
  detected_gap: string | null;
  proposed_kb_article_id: string | null;
  proposed_kb_title: string | null;
  final_status: string | null;
  created_at: string;
}

export interface ReviewResponse {
  id: string;
  final_status: string;
  kb_article_status: string | null;
}

// --- Dashboard ---

export interface CategoryCount {
  name: string;
  count: number;
}

export interface DashboardMetrics {
  knowledge_base: {
    total_articles: number;
    by_source_type: Record<string, number>;
    by_status: Record<string, number>;
    articles_with_embeddings: number;
    categories: CategoryCount[];
  };
  learning: {
    total_events: number;
    by_status: Record<string, number>;
    approval_rate: number;
  };
  tickets: {
    total: number;
    by_priority: Record<string, number>;
    by_root_cause: CategoryCount[];
  };
  scripts: {
    total: number;
    by_category: CategoryCount[];
  };
}

// --- Detect Gap ---

export interface ProposedArticle {
  id: string;
  title: string;
  body: string;
  status: string;
}

export interface DetectGapResponse {
  gap_detected: boolean;
  learning_event_id: string | null;
  detected_gap: string | null;
  proposed_article: ProposedArticle | null;
}

// --- Copilot ---

export interface Classification {
  answer_type: string;
  confidence: number;
  reasoning: string;
}

export interface ProvenanceInfo {
  created_from_ticket: string | null;
  created_from_conversation: string | null;
  references_script: string | null;
}

export interface SearchResult {
  rank: number;
  source_type: string;
  source_id: string;
  title: string;
  content_preview: string;
  similarity_score: number;
  category: string | null;
  placeholders: string[] | null;
  provenance: ProvenanceInfo | null;
}

export interface CopilotResponse {
  classification: Classification;
  results: SearchResult[];
  metadata: Record<string, unknown>;
}

export const api = {
  login: async (email: string, password: string): Promise<TokenResponse> => {
    const body = new URLSearchParams({ username: email, password });
    const res = await fetch(`${API_BASE}/api/v1/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new ApiError(res.status, data.detail || 'Login failed');
    }

    return res.json();
  },

  register: async (email: string, password: string, fullName?: string): Promise<User> => {
    return request<User>('/api/v1/users/', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName || null }),
    });
  },

  getMe: async (): Promise<User> => {
    return request<User>('/api/v1/users/me');
  },

  // Knowledge Base
  listKBArticles: async (params: {
    search?: string;
    source_type?: string;
    category?: string;
    status?: string;
    page?: number;
    page_size?: number;
  } = {}): Promise<PaginatedResponse<KBArticleListItem>> => {
    const searchParams = new URLSearchParams();
    if (params.search) searchParams.set('search', params.search);
    if (params.source_type) searchParams.set('source_type', params.source_type);
    if (params.category) searchParams.set('category', params.category);
    if (params.status) searchParams.set('status', params.status);
    if (params.page) searchParams.set('page', String(params.page));
    if (params.page_size) searchParams.set('page_size', String(params.page_size));
    const qs = searchParams.toString();
    return request<PaginatedResponse<KBArticleListItem>>(`/api/v1/knowledge/${qs ? `?${qs}` : ''}`);
  },

  getKBArticle: async (id: string): Promise<KBArticleDetail> => {
    return request<KBArticleDetail>(`/api/v1/knowledge/${id}`);
  },

  // Learning Feed
  listLearningEvents: async (params: {
    status?: string;
    page?: number;
    page_size?: number;
  } = {}): Promise<PaginatedResponse<LearningEvent>> => {
    const searchParams = new URLSearchParams();
    if (params.status) searchParams.set('status_filter', params.status);
    if (params.page) searchParams.set('page', String(params.page));
    if (params.page_size) searchParams.set('page_size', String(params.page_size));
    const qs = searchParams.toString();
    return request<PaginatedResponse<LearningEvent>>(`/api/v1/learning/events${qs ? `?${qs}` : ''}`);
  },

  reviewLearningEvent: async (eventId: string, decision: 'Approved' | 'Rejected'): Promise<ReviewResponse> => {
    return request<ReviewResponse>(`/api/v1/learning/review/${eventId}`, {
      method: 'POST',
      body: JSON.stringify({ decision }),
    });
  },

  // Dashboard
  getDashboardMetrics: async (): Promise<DashboardMetrics> => {
    return request<DashboardMetrics>('/api/v1/dashboard/metrics');
  },

  // Learning — Detect Gap
  detectGap: async (ticketId: string): Promise<DetectGapResponse> => {
    return request<DetectGapResponse>('/api/v1/learning/detect-gap', {
      method: 'POST',
      body: JSON.stringify({ ticket_id: ticketId }),
    });
  },

  // Copilot
  copilotAsk: async (question: string): Promise<CopilotResponse> => {
    return request<CopilotResponse>('/api/v1/copilot/ask', {
      method: 'POST',
      body: JSON.stringify({ question }),
    });
  },
};
