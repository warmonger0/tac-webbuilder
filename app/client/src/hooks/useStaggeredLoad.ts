import { useEffect, useState } from 'react';

/**
 * Hook to stagger component initialization for better initial load performance.
 *
 * Instead of loading all components simultaneously on page load, this hook
 * delays component initialization by a specified amount of milliseconds.
 * This prevents the "thundering herd" problem where all API calls fire at once.
 *
 * @param delayMs - Delay in milliseconds before enabling the component
 * @returns boolean indicating whether the component should be active
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const isReady = useStaggeredLoad(500);
 *
 *   if (!isReady) {
 *     return <Skeleton />;
 *   }
 *
 *   return <ActualComponent />;
 * }
 * ```
 */
export function useStaggeredLoad(delayMs: number): boolean {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsReady(true);
    }, delayMs);

    return () => clearTimeout(timer);
  }, [delayMs]);

  return isReady;
}
