/**
 * Cabinet State Management
 * Handles persistent storage of cabinet ingredients using localStorage
 */

const CABINET_STORAGE_KEY = 'cocktail-cache-cabinet';

/**
 * Save cabinet ingredients to localStorage
 * @param {string[]} ingredients - Array of ingredient IDs
 */
function saveCabinet(ingredients) {
    try {
        localStorage.setItem(CABINET_STORAGE_KEY, JSON.stringify(ingredients));
        // Dispatch custom event for same-tab updates (e.g., nav indicator)
        window.dispatchEvent(new CustomEvent('cabinet-updated'));
        return true;
    } catch (error) {
        console.error('Failed to save cabinet to localStorage:', error);
        return false;
    }
}

/**
 * Load cabinet ingredients from localStorage
 * @returns {string[]} Array of ingredient IDs, empty array if none saved
 */
function loadCabinet() {
    try {
        const stored = localStorage.getItem(CABINET_STORAGE_KEY);
        if (stored) {
            const parsed = JSON.parse(stored);
            // Validate that it's an array of strings
            if (Array.isArray(parsed) && parsed.every(item => typeof item === 'string')) {
                return parsed;
            }
        }
        return [];
    } catch (error) {
        console.error('Failed to load cabinet from localStorage:', error);
        return [];
    }
}

/**
 * Clear cabinet from localStorage
 */
function clearCabinet() {
    try {
        localStorage.removeItem(CABINET_STORAGE_KEY);
        // Dispatch custom event for same-tab updates (e.g., nav indicator)
        window.dispatchEvent(new CustomEvent('cabinet-updated'));
        return true;
    } catch (error) {
        console.error('Failed to clear cabinet from localStorage:', error);
        return false;
    }
}

/**
 * Check if cabinet has any saved ingredients
 * @returns {boolean}
 */
function hasSavedCabinet() {
    const cabinet = loadCabinet();
    return cabinet.length > 0;
}

// Export for module usage (if needed in future)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { saveCabinet, loadCabinet, clearCabinet, hasSavedCabinet };
}
