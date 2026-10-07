import { useEffect, useState } from 'react'
import type { MediaAsset } from '../types/media'

import { API_BASE_URL } from '../../../lib/env'
import { useAuth } from '../../auth/hooks/useAuth'

export function MediaPreview({ asset }: { asset: MediaAsset }) {
  const { accessToken } = useAuth()
  const [source, setSource] = useState<string>()

  useEffect(() => {
    let objectUrl: string | undefined
    const load = async () => {
      if (!accessToken) return
      const response = await fetch(`${API_BASE_URL}${asset.content_url}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      if (!response.ok) return
      objectUrl = URL.createObjectURL(await response.blob())
      setSource(objectUrl)
    }
    void load()
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [accessToken, asset.content_url])

  if (!source) return <div style={{ minHeight: '120px' }}>Loading preview...</div>
  if (asset.media_kind === 'VIDEO') {
    return <video src={source} controls style={{ maxWidth: '100%', maxHeight: '220px' }} />
  }
  return <img src={source} alt={asset.original_filename} style={{ maxWidth: '100%', maxHeight: '220px', objectFit: 'contain' }} />
}
