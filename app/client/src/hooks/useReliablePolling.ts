import { useEffect, useRef, useState, useCallback } from 'react';
import { intervals } from '../config/intervals';

interface ReliablePollingOptions<T> {
  fetchFn: () => Promise<T>;
  onSuccess: (data: T) => void;
  onError?: (error: Error) => void;
  enabled?: boolean;
  interval?: number;
  adaptiveInterval?: boolean;
  minInterval?: number;
  maxInterval?: number;
  maxConsecutiveErrors?: number;
}

interface PollingState {
  isPolling: boolean;
  connectionQuality: 'excellent' | 'good' | 'poor' | 'disconnected';
  lastUpdated: Date | null;
  consecutiveErrors: number;
  currentInterval: number;
}

/**
 * Reliable polling hook with:
 * - Adaptive polling interval (slows down during errors)
 * - Visibility API integration (pauses when hidden)
 * - Connection quality monitoring
 * - Maximum error threshold
 * - Error recovery
 */
export function useReliablePolling<T>({
  fetchFn,
  onSuccess,
  onError,
  enabled = true,
  interval = intervals.polling.defaultInterval,
  adaptiveInterval = true,
  minInterval = intervals.polling.minInterval,
  maxInterval = intervals.polling.maxInterval,
  maxConsecutiveErrors = intervals.polling.maxConsecutiveErrors,
}: ReliablePollingOptions<T>) {
  const [state, setState] = useState<PollingState>({
    isPolling: false,
    connectionQuality: 'disconnected',
    lastUpdated: null,
    consecutiveErrors: 0,
    currentInterval: interval,
  });

  const intervalRef = useRef<NodeJS.Timeout>();
  const consecutiveErrorsRef = useRef(0);
  const isPageVisibleRef = useRef(true);
  const lastSuccessTimeRef = useRef<number>(Date.now());

  // Use refs for callbacks to avoid recreating fetch on every render
  const fetchFnRef = useRef(fetchFn);
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);

  // Update refs when callbacks change
  useEffect(() => {
    fetchFnRef.current = fetchFn;
  }, [fetchFn]);

  useEffect(() => {
    onSuccessRef.current = onSuccess;
  }, [onSuccess]);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  // Calculate adaptive interval based on consecutive errors
  const getAdaptiveInterval = useCallback((errors: number): number => {
    if (!adaptiveInterval) {
      return interval;
    }

    // Increase interval exponentially with errors
    const multiplier = Math.pow(intervals.polling.backoffMultiplier, Math.min(errors, 5));
    const adaptedInterval = Math.min(interval * multiplier, maxInterval);
    return Math.max(adaptedInterval, minInterval);
  }, [adaptiveInterval, interval, minInterval, maxInterval]);

  // Calculate connection quality based on error rate and recency
  const updateConnectionQuality = useCallback((errors: number, lastSuccess: number): 'excellent' | 'good' | 'poor' | 'disconnected' => {
    const timeSinceLastSuccess = Date.now() - lastSuccess;

    if (errors >= maxConsecutiveErrors) {
      return 'disconnected';
    }

    if (errors === 0 && timeSinceLastSuccess < 10000) {
      return 'excellent';
    }

    if (errors <= 1 && timeSinceLastSuccess < 30000) {
      return 'good';
    }

    if (errors <= 3 && timeSinceLastSuccess < 60000) {
      return 'poor';
    }

    return 'disconnected';
  }, [maxConsecutiveErrors]);

  // Fetch data
  const fetch = useCallback(async () => {
    if (!enabled || !isPageVisibleRef.current) {
      return;
    }

    // Stop polling if we've exceeded max consecutive errors
    if (consecutiveErrorsRef.current >= maxConsecutiveErrors) {
      console.warn(`[Polling] Max consecutive errors (${maxConsecutiveErrors}) reached, stopping polling`);
      setState((prev) => ({
        ...prev,
        isPolling: false,
        connectionQuality: 'disconnected',
      }));
      return;
    }

    try {
      const data = await fetchFnRef.current();

      // Success: reset error count and update state
      consecutiveErrorsRef.current = 0;
      lastSuccessTimeRef.current = Date.now();

      setState({
        isPolling: true,
        connectionQuality: 'excellent',
        lastUpdated: new Date(),
        consecutiveErrors: 0,
        currentInterval: interval,
      });

      onSuccessRef.current(data);
    } catch (error) {
      // Error: increment error count and adapt interval
      consecutiveErrorsRef.current++;
      const adaptedInterval = getAdaptiveInterval(consecutiveErrorsRef.current);

      setState((prev) => ({
        ...prev,
        isPolling: true,
        connectionQuality: updateConnectionQuality(consecutiveErrorsRef.current, lastSuccessTimeRef.current),
        consecutiveErrors: consecutiveErrorsRef.current,
        currentInterval: adaptedInterval,
      }));

      console.error('[Polling] Error fetching data:', error);
      onErrorRef.current?.(error as Error);
    }
  }, [enabled, interval, getAdaptiveInterval, updateConnectionQuality, maxConsecutiveErrors]);


  // Handle visibility change
  useEffect(() => {
    const handleVisibilityChange = () => {
      const isVisible = document.visibilityState === 'visible';
      isPageVisibleRef.current = isVisible;

      if (isVisible && enabled) {
        console.log('[Polling] Page visible, resuming polling...');
        // Reset error count on visibility change
        consecutiveErrorsRef.current = 0;
        setState((prev) => ({
          ...prev,
          consecutiveErrors: 0,
          currentInterval: interval,
        }));
        // Don't call startPolling here - let the main polling effect handle it
      } else if (!isVisible) {
        console.log('[Polling] Page hidden, pausing polling');
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = undefined;
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [enabled, interval]);

  // Initial polling and cleanup
  useEffect(() => {
    if (!enabled) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = undefined;
      }
      setState((prev) => ({ ...prev, isPolling: false }));
      return;
    }

    // Add random stagger delay (0-2 seconds) to prevent thundering herd
    // while maintaining responsive initial load
    const staggerDelay = Math.random() * 2000;
    const timeoutId = setTimeout(() => {
      // Initial fetch
      fetch();

      // Set up interval
      intervalRef.current = setInterval(() => {
        fetch();
      }, interval);
    }, staggerDelay);

    return () => {
      clearTimeout(timeoutId);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = undefined;
      }
    };
  }, [enabled, fetch, interval]);

  // Note: Adaptive interval is tracked in state for display purposes,
  // but the actual polling interval remains constant to avoid re-render loops

  // Manual retry function
  const retry = useCallback(() => {
    console.log('[Polling] Manual retry triggered');
    consecutiveErrorsRef.current = 0;
    setState((prev) => ({
      ...prev,
      consecutiveErrors: 0,
      currentInterval: interval,
    }));
    fetch();
  }, [interval, fetch]);

  return { ...state, retry };
}
