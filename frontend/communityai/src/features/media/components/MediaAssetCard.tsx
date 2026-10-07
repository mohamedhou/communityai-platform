import type { MediaAsset } from '../types/media'
import { MediaPreview } from './MediaPreview'

export function MediaAssetCard({ asset, selected, onSelect, onDelete }: {
  asset: MediaAsset
  selected?: boolean
  onSelect?: () => void
  onDelete?: () => void
}) {
  return (
    <article style={{ border: selected ? '2px solid #2563eb' : '1px solid #e5e7eb', padding: '12px', borderRadius: '8px' }}>
      <MediaPreview asset={asset} />
      <p style={{ overflowWrap: 'anywhere' }}>{asset.original_filename}</p>
      {onSelect && <button type="button" onClick={onSelect}>{selected ? 'Selected' : 'Select'}</button>}{' '}
      {onDelete && <button type="button" onClick={onDelete}>Delete</button>}
    </article>
  )
}
