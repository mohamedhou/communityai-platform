export function UploadProgress({ value }: { value: number }) {
  return (
    <div aria-label={`Upload progress ${value}%`} style={{ marginTop: '8px' }}>
      <progress value={value} max={100} style={{ width: '100%' }} />
      <small>{value}% uploaded</small>
    </div>
  )
}
