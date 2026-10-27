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
    <div className="media-uploader-box">
      <label htmlFor="media-upload" className="media-uploader-label">
        <span className="media-upload-icon">☁️</span>
        <span className="media-upload-title">Drop your image or video here, or click to browse</span>
        <span className="media-upload-sub">Supports JPEG, PNG, WebP, GIF, MP4, WebM (up to 100MB)</span>
      </label>
      <input
        id="media-upload"
        type="file"
        className="media-file-input"
        accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm"
        onChange={handleChange}
        disabled={upload.isPending}
      />
      {upload.isPending && (
        <div className="media-upload-progress">
          <UploadProgress value={progress} />
        </div>
      )}
      {upload.isError && (
        <div className="inbox-banner-alert banner-error" role="alert" style={{ marginTop: '12px' }}>
          {(upload.error as Error).message}
        </div>
      )}
      {upload.isSuccess && (
        <div className="inbox-banner-alert banner-success" role="status" style={{ marginTop: '12px' }}>
          Asset uploaded successfully.
        </div>
      )}
    </div>
  )
}
