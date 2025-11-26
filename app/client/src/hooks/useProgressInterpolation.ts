import { useEffect, useState, useRef } from 'react';

/**
 * Hook to smoothly interpolate progress values over 500ms
 * Uses requestAnimationFrame for smooth 60fps animations
 *
 * @param targetProgress - The target progress value to interpolate to
 * @returns The current interpolated progress value
 */
export function useProgressInterpolation(targetProgress: number): number {
  const [interpolatedProgress, setInterpolatedProgress] = useState(targetProgress);
  const animationRef = useRef<number | null>(null);
  const startProgressRef = useRef(targetProgress);
  const startTimeRef = useRef<number | null>(null);

  useEffect(() => {
    // If target hasn't changed, no need to animate
    if (targetProgress === interpolatedProgress) {
      return;
    }

    // Store starting values
    startProgressRef.current = interpolatedProgress;
    startTimeRef.current = null;

    const duration = 500; // 500ms animation duration

    const animate = (currentTime: number) => {
      // Initialize start time on first frame
      if (startTimeRef.current === null) {
        startTimeRef.current = currentTime;
      }

      const elapsed = currentTime - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1); // 0 to 1

      // Ease-in-out interpolation for smooth motion
      const easeInOutCubic = progress < 0.5
        ? 4 * progress * progress * progress
        : 1 - Math.pow(-2 * progress + 2, 3) / 2;

      const currentValue = startProgressRef.current + (targetProgress - startProgressRef.current) * easeInOutCubic;
      setInterpolatedProgress(currentValue);

      // Continue animation if not complete
      if (progress < 1) {
        animationRef.current = requestAnimationFrame(animate);
      } else {
        // Ensure we end exactly at target
        setInterpolatedProgress(targetProgress);
        animationRef.current = null;
      }
    };

    // Start animation
    animationRef.current = requestAnimationFrame(animate);

    // Cleanup on unmount or when target changes
    return () => {
      if (animationRef.current !== null) {
        cancelAnimationFrame(animationRef.current);
        animationRef.current = null;
      }
    };
  }, [targetProgress]);

  return interpolatedProgress;
}
