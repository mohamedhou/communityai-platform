import type { MediaAsset } from '../types/media'
import { useMediaLibrary } from '../hooks/useMedia'
import { MediaAssetCard } from './MediaAssetCard'
import { MediaUploader } from './MediaUploader'

export function MediaPicker({ value, onChange }: { value: MediaAsset | null; onChange: (asset: MediaAsset | null) => void }) {
  const media = useMediaLibrary()
  return (
    <section style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <MediaUploader onUploaded={onChange} />
      {media.isLoading && <p>Loading media library...</p>}
      {media.isError && <p role="alert">{(media.error as Error).message}</p>}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '12px' }}>
        {media.data?.map((asset) => (
          <MediaAssetCard key={asset.id} asset={asset} selected={value?.id === asset.id} onSelect={() => onChange(asset)} />
        ))}
      </div>
      {value && <button type="button" onClick={() => onChange(null)}>Remove selected media</button>}
    </section>
  )
}
