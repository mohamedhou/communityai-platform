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
    <main className="page-shell media-page">
      <div className="management-container">
        <div className="page-header-row">
          <div>
            <p className="eyebrow">Asset Management</p>
            <h1>Media Library</h1>
            <p className="page-subtitle">
              Upload, organize, and manage images and videos across your workspace.
            </p>
          </div>
        </div>

        <div className="media-uploader-section">
          <MediaUploader />
        </div>

        {media.isLoading && (
          <div className="media-loading-state">
            <p>Loading media assets...</p>
          </div>
        )}

        {media.isError && (
          <div className="inbox-banner-alert banner-error" role="alert">
            {(media.error as Error).message}
          </div>
        )}

        {media.data && media.data.length === 0 && !media.isLoading && (
          <div className="media-empty-state">
            <span className="media-empty-icon">📁</span>
            <h3>No media assets yet</h3>
            <p>Upload images or videos above to use them in your social publications.</p>
          </div>
        )}

        <div className="media-grid">
          {media.data?.map((asset) => (
            <MediaAssetCard
              key={asset.id}
              asset={asset}
              onDelete={() => setPendingDelete(asset)}
            />
          ))}
        </div>

        {pendingDelete && (
          <DeleteMediaDialog
            asset={pendingDelete}
            onCancel={() => setPendingDelete(null)}
            onConfirm={() =>
              deleteMedia.mutate(pendingDelete.id, {
                onSuccess: () => setPendingDelete(null),
              })
            }
            isDeleting={deleteMedia.isPending}
          />
        )}
      </div>
    </main>
  )
}
