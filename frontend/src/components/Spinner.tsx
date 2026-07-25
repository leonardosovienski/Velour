export function Spinner({ size = 24 }: { size?: number }) {
  return (
    <div
      style={{ width: size, height: size }}
      className="border-2 border-border border-t-gold rounded-full animate-spin"
    />
  )
}

export function PageSpinner() {
  return (
    <div className="flex items-center justify-center h-64">
      <Spinner size={36} />
    </div>
  )
}
