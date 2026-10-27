import type { MediaAsset } from '../types/media'
import { MediaPreview } from './MediaPreview'

export function MediaAssetCard({
  asset,
  selected,
  onSelect,
  onDelete,
}: {
  asset: MediaAsset
  selected?: boolean
  onSelect?: () => void
  onDelete?: () => void
}) {
  return (
    <article className={`media-asset-card ${selected ? 'selected' : ''}`}>
      <div className="media-asset-preview-container">
        <MediaPreview asset={asset} />
      </div>
      <p className="media-asset-filename" title={asset.original_filename}>
        {asset.original_filename}
      </p>
      <div className="media-asset-actions">
        {onSelect && (
          <button
            type="button"
            className={`btn-action ${selected ? 'active' : ''}`}
            onClick={onSelect}
          >
            {selected ? 'Selected' : 'Select'}
          </button>
        )}
        {onDelete && (
          <button
            type="button"
            className="btn-danger-outline"
            onClick={onDelete}
          >
            Delete
          </button>
        )}
      </div>
    </article>
  )
}
