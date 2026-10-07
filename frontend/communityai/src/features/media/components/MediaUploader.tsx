import { useState } from 'react'
import type { ChangeEvent } from 'react'
import { useUploadMedia } from '../hooks/useMedia'
import type { MediaAsset } from '../types/media'
import { UploadProgress } from './UploadProgress'

export function MediaUploader({ onUploaded }: { onUploaded?: (asset: MediaAsset) => void }) {
  const [progress, setProgress] = useState(0)
  const upload = useUploadMedia(setProgress)
  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    setProgress(0)
    upload.mutate(file, { onSuccess: onUploaded })
  }
  return (
    <div>
      <label htmlFor="media-upload">Upload image or video</label>
      <input id="media-upload" type="file" accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm" onChange={handleChange} disabled={upload.isPending} />
      {upload.isPending && <UploadProgress value={progress} />}
      {upload.isError && <p role="alert">{(upload.error as Error).message}</p>}
      {upload.isSuccess && <p role="status">Upload complete.</p>}
    </div>
  )
}
