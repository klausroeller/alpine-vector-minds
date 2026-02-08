const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public endpoint?: string,
    public method?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }

  /** Formatted message with context for debugging */
  get debugMessage(): string {
    const parts: string[] = [];
    if (this.method && this.endpoint) {
      parts.push(`${this.method} ${this.endpoint}`);
    }
    parts.push(`[${this.status}] ${this.message}`);
    return parts.join(' — ');
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const method = (options.method || 'GET').toUpperCase();
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });
  } catch (err) {
    throw new ApiError(
      0,
      `Network error: ${err instanceof Error ? err.message : 'Failed to connect'}`,
      path,
      method,
    );
  }

  if (res.status === 401) {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    throw new ApiError(401, 'Session expired — please log in again', path, method);
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: `HTTP ${res.status} ${res.statusText}` }));
    const detail = body.detail || `HTTP ${res.status} ${res.statusText}`;
    throw new ApiError(res.status, detail, path, method);
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
  qa?: {
    total_scored: number;
    average_score: number;
    red_flag_count: number;
  };
  evaluation?: {
    classification_accuracy: number;
    hit_at_1: number;
    hit_at_5: number;
    hit_at_10: number;
    total_questions: number;
    evaluated_at: string;
  };
  feedback?: {
    total_feedback: number;
    helpful_count: number;
    helpful_rate: number;
  };
}

// --- QA Scores ---

export interface CategoryScore {
  score: number;
  weight: number;
  feedback: string;
}

export interface QAScoreResponse {
  conversation_id: string;
  overall_score: number | null;
  categories: Record<string, CategoryScore>;
  red_flags: string[];
  summary: string;
  scored_at: string | null;
}

export interface QAScoreListItem {
  conversation_id: string;
  ticket_id: string;
  agent_name: string | null;
  channel: string | null;
  overall_score: number | null;
  red_flags: string[];
  scored_at: string | null;
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

export interface AIAnswer {
  text: string;
  source_ids: string[];
}

export interface CopilotResponse {
  classification: Classification;
  ai_answer: AIAnswer | null;
  results: SearchResult[];
  metadata: Record<string, unknown>;
}

// --- Deep Research ---

export interface SubQueryInfo {
  query: string;
  pool: string;
  aspect: string;
}

export interface EvidenceItem {
  source_id: string;
  source_type: string;
  title: string;
  relevance: string;
  content_preview: string;
}

export interface RelatedResource {
  source_id: string;
  source_type: string;
  title: string;
  why_relevant: string;
}

export interface ResearchReport {
  summary: string;
  evidence: EvidenceItem[];
  related_resources: RelatedResource[];
}

export interface CopilotResearchResponse {
  mode: 'simple' | 'research';
  classification?: Classification;
  results?: SearchResult[];
  report?: ResearchReport;
  sub_queries?: SubQueryInfo[];
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

  copilotResearch: async (question: string): Promise<CopilotResearchResponse> => {
    return request<CopilotResearchResponse>('/api/v1/copilot/research', {
      method: 'POST',
      body: JSON.stringify({ question }),
    });
  },

  // QA Scoring
  scoreConversation: async (conversationId: string): Promise<QAScoreResponse> => {
    return request<QAScoreResponse>(`/api/v1/qa/score/${conversationId}`, {
      method: 'POST',
    });
  },

  getQADetail: async (conversationId: string): Promise<QAScoreResponse> => {
    return request<QAScoreResponse>(`/api/v1/qa/detail/${conversationId}`);
  },

  listConversations: async (params: {
    scored?: boolean;
    page?: number;
    page_size?: number;
  } = {}): Promise<PaginatedResponse<QAScoreListItem>> => {
    const searchParams = new URLSearchParams();
    if (params.scored !== undefined) searchParams.set('scored', String(params.scored));
    if (params.page) searchParams.set('page', String(params.page));
    if (params.page_size) searchParams.set('page_size', String(params.page_size));
    const qs = searchParams.toString();
    return request<PaginatedResponse<QAScoreListItem>>(`/api/v1/qa/conversations${qs ? `?${qs}` : ''}`);
  },

  listQAScores: async (params: {
    min_score?: number;
    has_red_flags?: boolean;
    page?: number;
    page_size?: number;
  } = {}): Promise<PaginatedResponse<QAScoreListItem>> => {
    const searchParams = new URLSearchParams();
    if (params.min_score !== undefined) searchParams.set('min_score', String(params.min_score));
    if (params.has_red_flags !== undefined) searchParams.set('has_red_flags', String(params.has_red_flags));
    if (params.page) searchParams.set('page', String(params.page));
    if (params.page_size) searchParams.set('page_size', String(params.page_size));
    const qs = searchParams.toString();
    return request<PaginatedResponse<QAScoreListItem>>(`/api/v1/qa/scores${qs ? `?${qs}` : ''}`);
  },

  // Copilot Feedback
  submitFeedback: async (params: {
    question_text: string;
    classification?: string;
    result_id?: string;
    result_rank?: number;
    helpful: boolean;
  }): Promise<{ id: string; status: string }> => {
    return request<{ id: string; status: string }>('/api/v1/copilot/feedback', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },
};
