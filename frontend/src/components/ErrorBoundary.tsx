import { Component, type ReactNode } from 'react'
import { logError } from '../lib/errorLogging'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: unknown) {
    logError(error, 'ErrorBoundary')
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-bg flex items-center justify-center p-6">
          <div className="max-w-md text-center space-y-3">
            <h1 className="font-display text-xl font-semibold text-cream">Algo deu errado</h1>
            <p className="text-muted text-sm">
              Ocorreu um erro inesperado. Tente recarregar a página; se o problema continuar, avise a equipe técnica.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="bg-gold text-bg font-semibold px-5 py-2 rounded-lg text-sm"
            >
              Recarregar
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
