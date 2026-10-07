import { useState } from 'react'
import { useDeleteMedia, useMediaLibrary } from '../hooks/useMedia'
import { DeleteMediaDialog } from '../components/DeleteMediaDialog'
import { MediaAssetCard } from '../components/MediaAssetCard'
import { MediaUploader } from '../components/MediaUploader'
import type { MediaAsset } from '../types/media'

export function MediaLibraryPage() {
  const media = useMediaLibrary()
  const deleteMedia = useDeleteMedia()
  const [pendingDelete, setPendingDelete] = useState<MediaAsset | null>(null)
  return (
    <main className="page-shell">
      <div className="social-container">
        <h1>Media Library</h1>
        <p className="page-subtitle">Upload and manage workspace images and videos.</p>
        <MediaUploader />
        {media.isLoading && <p>Loading media library...</p>}
        {media.isError && <p role="alert">{(media.error as Error).message}</p>}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '16px', marginTop: '24px' }}>
          {media.data?.map((asset) => (
            <MediaAssetCard key={asset.id} asset={asset} onDelete={() => setPendingDelete(asset)} />
          ))}
        </div>
        {pendingDelete && (
          <DeleteMediaDialog
            asset={pendingDelete}
            onCancel={() => setPendingDelete(null)}
            onConfirm={() => deleteMedia.mutate(pendingDelete.id, { onSuccess: () => setPendingDelete(null) })}
            isDeleting={deleteMedia.isPending}
          />
        )}
      </div>
    </main>
  )
}
