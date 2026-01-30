import { useState, useEffect, useRef } from 'react'

export default function usePolling(fetchFn, interval = 3000) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const timeoutRef = useRef(null)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    let pollCount = 0
    
    async function poll() {
      try {
        // Only show loading on initial fetch
        if (pollCount === 0) {
          setLoading(true)
        }
        
        const res = await fetchFn()
        
        if (!mountedRef.current) return
        
        setData(res)
        
        if (pollCount === 0) {
          setLoading(false)
        }
        
        pollCount++
        
        // Continue polling if no data or empty array
        if (!res || res.length === 0) {
          timeoutRef.current = setTimeout(poll, interval)
        }
      } catch (error) {
        console.error('Polling error:', error)
        if (mountedRef.current) {
          setLoading(false)
        }
      }
    }
    
    poll()
    
    return () => {
      mountedRef.current = false
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [fetchFn, interval])

  return { data, loading }
}
