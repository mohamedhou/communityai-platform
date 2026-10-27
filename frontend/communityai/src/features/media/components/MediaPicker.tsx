import type { MediaAsset } from '../types/media'
import { useMediaLibrary } from '../hooks/useMedia'
import { MediaAssetCard } from './MediaAssetCard'
import { MediaUploader } from './MediaUploader'

export function MediaPicker({
  value,
  onChange,
}: {
  value: MediaAsset | null
  onChange: (asset: MediaAsset | null) => void
}) {
  const media = useMediaLibrary()
  return (
    <section className="media-picker-section">
      <MediaUploader onUploaded={onChange} />
      {media.isLoading && <p className="media-loading-text">Loading media library...</p>}
      {media.isError && (
        <p role="alert" className="inbox-banner-alert banner-error">
          {(media.error as Error).message}
        </p>
      )}
      <div className="media-grid media-grid-compact">
        {media.data?.map((asset) => (
          <MediaAssetCard
            key={asset.id}
            asset={asset}
            selected={value?.id === asset.id}
            onSelect={() => onChange(asset)}
          />
        ))}
      </div>
      {value && (
        <button
          type="button"
          className="btn-secondary"
          style={{ alignSelf: 'flex-start', marginTop: '8px' }}
          onClick={() => onChange(null)}
        >
          ✕ Remove selected media
        </button>
      )}
    </section>
  )
}
