// Barrel export for backward compatibility
// This file maintains the original RequestForm export while delegating to the new split components

export { RequestFormCore as RequestForm } from './RequestFormCore';
export { RequestFormPreview } from './RequestFormPreview';
export { useRequestForm } from './RequestFormHooks';

// Re-export types
export type { UseRequestFormReturn } from './RequestFormHooks';
export type { RequestFormPreviewProps } from './RequestFormPreview';
