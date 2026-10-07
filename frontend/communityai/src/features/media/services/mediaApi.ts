import { API_BASE_URL } from '../../../lib/env'
import type { MediaAsset } from '../types/media'

const API_BASE = `${API_BASE_URL}/api/v1/media`

function parseError(response: Response, fallback: string) {
  return response.json().catch(() => ({ detail: fallback })).then((body) => new Error(body.detail || fallback))
}

export async function listMedia(token: string): Promise<MediaAsset[]> {
  const response = await fetch(API_BASE, { headers: { Authorization: `Bearer ${token}` } })
  if (!response.ok) throw await parseError(response, 'Failed to load media library')
  return response.json()
}

export async function getMediaContentUrl(token: string, asset: MediaAsset): Promise<string> {
  // The content endpoint is authenticated; callers should use the URL only from an authenticated session.
  void token
  return `${API_BASE_URL}${asset.content_url}`
}

export function uploadMedia(
  token: string,
  file: File,
  onProgress?: (value: number) => void,
): Promise<MediaAsset> {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest()
    request.open('POST', API_BASE)
    request.setRequestHeader('Authorization', `Bearer ${token}`)
    request.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress?.(Math.round((event.loaded / event.total) * 100))
    }
    request.onerror = () => reject(new Error('Upload failed'))
    request.onload = () => {
      if (request.status < 200 || request.status >= 300) {
        try {
          reject(new Error(JSON.parse(request.responseText).detail || 'Upload failed'))
        } catch {
          reject(new Error('Upload failed'))
        }
        return
      }
      resolve(JSON.parse(request.responseText) as MediaAsset)
    }
    const body = new FormData()
    body.append('file', file)
    request.send(body)
  })
}

export async function deleteMedia(token: string, mediaId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/${mediaId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) throw await parseError(response, 'Failed to delete media')
}
