import { API_BASE_URL } from '../../../lib/env';
import type { Post, PostApprovalStatus, PostStatus } from '../types/post';

const API_BASE = `${API_BASE_URL}/api/v1/posts`;

export async function getPosts(
  token: string,
  status?: PostStatus,
  approvalStatus?: PostApprovalStatus
): Promise<Post[]> {
  const params = new URLSearchParams();
  if (status) params.append('status_filter', status);
  if (approvalStatus) params.append('approval_status', approvalStatus);
  const query = params.toString();
  const url = query ? `${API_BASE}?${query}` : API_BASE;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to fetch posts' }));
    throw new Error(err.detail || 'Failed to fetch posts');
  }
  return res.json();
}

export async function getPost(token: string, postId: number): Promise<Post> {
  const res = await fetch(`${API_BASE}/${postId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to fetch post' }));
    throw new Error(err.detail || 'Failed to fetch post');
  }
  return res.json();
}

export async function createPost(
  token: string,
  payload: { content: string; social_account_id: number; media_url?: string }
): Promise<Post> {
  const res = await fetch(API_BASE, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to create post' }));
    throw new Error(err.detail || 'Failed to create post');
  }
  return res.json();
}

export async function updatePost(
  token: string,
  postId: number,
  payload: { content?: string; social_account_id?: number; media_url?: string }
): Promise<Post> {
  const res = await fetch(`${API_BASE}/${postId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to update post' }));
    throw new Error(err.detail || 'Failed to update post');
  }
  return res.json();
}

export async function deletePost(token: string, postId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/${postId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to delete post' }));
    throw new Error(err.detail || 'Failed to delete post');
  }
}

export async function publishPost(token: string, postId: number): Promise<Post> {
  const res = await fetch(`${API_BASE}/${postId}/publish`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to publish post' }));
    throw new Error(err.detail || 'Failed to publish post');
  }
  return res.json();
}

export async function schedulePost(token: string, postId: number, scheduledAt: string): Promise<Post> {
  const res = await fetch(`${API_BASE}/${postId}/schedule`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ scheduled_at: scheduledAt }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to schedule post' }));
    throw new Error(err.detail || 'Failed to schedule post');
  }
  return res.json();
}

export async function cancelPost(token: string, postId: number): Promise<Post> {
  const res = await fetch(`${API_BASE}/${postId}/cancel`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to cancel post' }));
    throw new Error(err.detail || 'Failed to cancel post');
  }
  return res.json();
}

export async function submitForReview(token: string, postId: number): Promise<Post> {
  const res = await fetch(`${API_BASE}/${postId}/submit-review`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to submit post for review' }));
    throw new Error(err.detail || 'Failed to submit post for review');
  }
  return res.json();
}

export async function approvePost(token: string, postId: number): Promise<Post> {
  const res = await fetch(`${API_BASE}/${postId}/approve`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to approve post' }));
    throw new Error(err.detail || 'Failed to approve post');
  }
  return res.json();
}

export async function rejectPost(token: string, postId: number, reason: string): Promise<Post> {
  const res = await fetch(`${API_BASE}/${postId}/reject`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ reason }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to reject post' }));
    throw new Error(err.detail || 'Failed to reject post');
  }
  return res.json();
}

export async function getReviewQueue(token: string): Promise<Post[]> {
  const res = await fetch(`${API_BASE}/review/queue`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to fetch review queue' }));
    throw new Error(err.detail || 'Failed to fetch review queue');
  }
  return res.json();
}

export async function getReviewHistory(token: string): Promise<Post[]> {
  const res = await fetch(`${API_BASE}/review/history`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to fetch review history' }));
    throw new Error(err.detail || 'Failed to fetch review history');
  }
  return res.json();
}
