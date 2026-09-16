export function LoadError({ message = 'Não foi possível carregar os dados. Tente novamente.', onRetry }: { message?: string; onRetry?: () => void }) {
  return <div role="alert" className="rounded-xl border border-danger/30 bg-danger/5 p-5 my-4">
    <p className="text-cream text-sm">{message}</p>
    <button className="secondary-button mt-4" onClick={onRetry || (() => window.location.reload())}>Tentar novamente</button>
  </div>
}
