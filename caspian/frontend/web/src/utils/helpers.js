/**
 * Utility functions for the chat application
 */

/**
 * Prevents form submission from causing page navigation
 * @param {Event} e - The form submission event
 * @returns {boolean} - Always returns false to prevent default form submission
 */
export const preventFormNavigation = (e) => {
  if (e) {
    e.preventDefault();
    e.stopPropagation();
  }
  return false;
};

/**
 * Safely parses JSON without throwing exceptions
 * @param {string} jsonString - The JSON string to parse
 * @param {any} fallback - Fallback value if parsing fails
 * @returns {any} - The parsed object or the fallback value
 */
export const safeJsonParse = (jsonString, fallback = null) => {
  try {
    return JSON.parse(jsonString);
  } catch (e) {
    console.error('Error parsing JSON:', e);
    return fallback;
  }
};

/**
 * Helper function to scroll to the bottom of a container
 * @param {HTMLElement} container - The container to scroll
 * @param {boolean} smooth - Whether to use smooth scrolling
 */
export const scrollToBottom = (container, smooth = true) => {
  if (container) {
    container.scrollTo({
      top: container.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto'
    });
  }
};
