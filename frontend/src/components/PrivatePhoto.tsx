import { useEffect, useState } from 'react'
import { photosApi } from '../api/client'

export function PrivatePhoto({ path, label }: { path: string; label: string }) {
  const [image, setImage] = useState<{ path: string; url: string } | null>(null)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    const controller = new AbortController()
    let url: string | undefined
    setFailed(false)
    photosApi.get(path, controller.signal).then(blob => {
      if (controller.signal.aborted) return
      url = URL.createObjectURL(blob)
      setImage({ path, url })
    }).catch(() => { if (!controller.signal.aborted) setFailed(true) })
    return () => { controller.abort(); if (url) URL.revokeObjectURL(url) }
  }, [path])
  return <figure className="w-32"><figcaption className="text-muted text-xs mb-1">{label}</figcaption>{image?.path === path ? <a href={image.url} target="_blank" rel="noopener noreferrer"><img src={image.url} alt={label} className="h-28 w-32 object-cover rounded-lg border border-border" /></a> : <p className="text-muted text-xs p-3 border border-border rounded-lg">{failed ? 'Foto indisponível' : 'Carregando foto…'}</p>}</figure>
}
