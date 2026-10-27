import type { MediaAsset } from '../types/media'

export function DeleteMediaDialog({
  asset,
  onCancel,
  onConfirm,
  isDeleting,
}: {
  asset: MediaAsset
  onCancel: () => void
  onConfirm: () => void
  isDeleting: boolean
}) {
  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal-dialog">
        <h3 className="modal-title">Delete Media</h3>
        <p className="modal-body-text">
          Are you sure you want to permanently delete{' '}
          <strong>{asset.original_filename}</strong>? This action cannot be undone.
        </p>
        <div className="modal-footer-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={onCancel}
            disabled={isDeleting}
          >
            Cancel
          </button>
          <button
            type="button"
            className="btn-danger"
            onClick={onConfirm}
            disabled={isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  )
}
