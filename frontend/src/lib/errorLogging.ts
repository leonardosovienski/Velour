interface ErrorLogEntry {
  timestamp: string
  message: string
  stack?: string
  context?: string
}

function emit(entry: ErrorLogEntry) {
  // Log estruturado (JSON) no console — sem depender de serviço externo.
  // Fica pronto para ser capturado por qualquer coletor de logs do navegador
  // ou encaminhado a um endpoint de telemetria no futuro, sem mudar o
  // formato de emissão.
  console.error(JSON.stringify(entry))
}

export function logError(error: unknown, context?: string) {
  const err = error instanceof Error ? error : new Error(String(error))
  emit({
    timestamp: new Date().toISOString(),
    message: err.message,
    stack: err.stack,
    context,
  })
}

export function installGlobalErrorLogging() {
  window.addEventListener('error', (event) => {
    logError(event.error ?? event.message, 'window.onerror')
  })
  window.addEventListener('unhandledrejection', (event) => {
    logError(event.reason, 'unhandledrejection')
  })
}
