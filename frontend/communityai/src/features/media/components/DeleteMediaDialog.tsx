import type { MediaAsset } from '../types/media'

export function DeleteMediaDialog({ asset, onCancel, onConfirm, isDeleting }: {
  asset: MediaAsset
  onCancel: () => void
  onConfirm: () => void
  isDeleting: boolean
}) {
  return (
    <div role="dialog" aria-modal="true" style={{ padding: '16px', border: '1px solid #fecaca', background: '#fff7f7' }}>
      <p>Delete <strong>{asset.original_filename}</strong>?</p>
      <button type="button" onClick={onCancel} disabled={isDeleting}>Cancel</button>{' '}
      <button type="button" onClick={onConfirm} disabled={isDeleting}>{isDeleting ? 'Deleting...' : 'Delete'}</button>
    </div>
  )
}
