/**
 * Application Constants
 *
 * This module exports application-wide constants including branding,
 * versioning, and core application identifiers.
 */

import type { AppConstants } from './types';

/**
 * Application constants
 */
export const constants: AppConstants = {
  /** Application name displayed in the UI */
  NAME: 'tac-webbuilder',

  /** Application tagline/description */
  TAGLINE: 'Build web apps with natural language',

  /** Application namespace used for localStorage prefixes and other identifiers */
  NAMESPACE: 'tac-webbuilder',

  /** Application version */
  VERSION: '1.0.0',
};

/**
 * Default export for convenient importing
 */
export default constants;
