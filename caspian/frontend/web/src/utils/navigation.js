/**
 * Additional utility functions to prevent navigation issues
 */

/**
 * Safely handles button clicks without causing page navigation
 * @param {Function} callback - The function to call when the button is clicked
 * @returns {Function} - A wrapped function that prevents navigation
 */
export const safeButtonClick = (callback) => {
  return (e) => {
    try {
      // Prevent any default behavior
      if (e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Also prevent native event behaviors as a safety measure
        if (e.nativeEvent) {
          e.nativeEvent.preventDefault();
          e.nativeEvent.stopPropagation();
          e.nativeEvent.stopImmediatePropagation();
        }
      }
      
      // Call the original callback within a try/catch
      if (typeof callback === 'function') {
        callback(e);
      }
    } catch (error) {
      console.error('Error in button click handler:', error);
    }
    
    // Return false to prevent form submission
    return false;
  };
};

/**
 * Prevents form submission from causing page navigation
 * @param {Event} e - The form submission event
 * @returns {boolean} - Always returns false to prevent default form submission
 */
export const preventFormNavigation = (e) => {
  if (e) {
    e.preventDefault();
    e.stopPropagation();
    
    // Additional deep prevention
    if (e.nativeEvent) {
      e.nativeEvent.preventDefault();
      e.nativeEvent.stopPropagation();
      e.nativeEvent.stopImmediatePropagation();
    }
  }
  return false;
};

/**
 * Adds a history entry to prevent navigating away on form submissions
 */
export const setupHistoryPushState = () => {
  // Only run once
  if (window._historyPushStateSetup) return;
  
  // Push a history state to prevent navigating away
  try {
    window.history.pushState({}, '', window.location.href);
    window.addEventListener('popstate', () => {
      window.history.pushState({}, '', window.location.href);
    });
    window._historyPushStateSetup = true;
    logEvent('History push state setup completed', {}, LogLevel.INFO);
  } catch (e) {
    logEvent('Failed to setup history push state', {
      error: e.toString(),
      stack: e.stack
    }, LogLevel.ERROR);
    console.error('Failed to setup history push state:', e);
  }
};

/**
 * Applies all navigation prevention techniques
 */
export const applyAllNavigationPrevention = () => {
  // Add a global click handler to prevent navigation for buttons inside forms
  document.addEventListener('click', (e) => {
    // Find closest button
    const button = e.target.closest('button');
    
    // Check if it's inside a form and doesn't have type="submit"
    if (button && 
        button.closest('form') && 
        button.type !== 'submit' &&
        !button.hasAttribute('data-allow-submit')) {
      e.preventDefault();
      e.stopPropagation();
      logEvent('Prevented potential navigation from button click', {
        button: button.outerHTML
      }, LogLevel.INFO);
      return false;
    }
  }, true);
  
  setupHistoryPushState();
};

// Run setup on import
if (typeof window !== 'undefined') {
  try {
    applyAllNavigationPrevention();
  } catch (error) {
    console.error('Error applying navigation prevention:', error);
  }
}
