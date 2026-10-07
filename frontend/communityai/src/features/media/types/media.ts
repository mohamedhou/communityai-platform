export type MediaKind = 'IMAGE' | 'VIDEO'

export interface MediaAsset {
  id: number
  workspace_id: number
  uploaded_by: number
  original_filename: string
  mime_type: string
  extension: string
  size_bytes: number
  checksum: string
  media_kind: MediaKind
  created_at: string
  updated_at: string
  content_url: string
}
