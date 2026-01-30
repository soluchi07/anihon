import { useState, useEffect } from 'react'

export default function usePolling(fetchFn, interval = 3000) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    async function poll() {
      setLoading(true)
      const res = await fetchFn()
      if (!mounted) return
      setData(res)
      setLoading(false)
      if (!res || res.length === 0) {
        setTimeout(poll, interval)
      }
    }
    poll()
    return () => { mounted = false }
  }, [fetchFn, interval])

  return { data, loading }
}
