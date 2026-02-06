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
};
