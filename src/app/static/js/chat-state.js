/**
 * Chat State Management
 * Handles persistent storage of chat history using sessionStorage
 * Uses sessionStorage (not localStorage) so chat resets on browser close
 */

const CHAT_STORAGE_KEY = 'cocktail-cache-chat';
const CHAT_SESSION_KEY = 'cocktail-cache-chat-session';

/**
 * Save chat state to sessionStorage
 * @param {string} messagesHtml - The innerHTML of the chat messages container
 * @param {string|null} sessionId - The chat session ID from the server
 */
function saveChatState(messagesHtml, sessionId) {
    try {
        sessionStorage.setItem(CHAT_STORAGE_KEY, messagesHtml);
        if (sessionId) {
            sessionStorage.setItem(CHAT_SESSION_KEY, sessionId);
        }
        return true;
    } catch (error) {
        console.error('Failed to save chat state:', error);
        return false;
    }
}

/**
 * Load chat state from sessionStorage
 * @returns {{messagesHtml: string|null, sessionId: string|null}}
 */
function loadChatState() {
    try {
        const messagesHtml = sessionStorage.getItem(CHAT_STORAGE_KEY);
        const sessionId = sessionStorage.getItem(CHAT_SESSION_KEY);
        return { messagesHtml, sessionId };
    } catch (error) {
        console.error('Failed to load chat state:', error);
        return { messagesHtml: null, sessionId: null };
    }
}

/**
 * Clear chat state from sessionStorage
 */
function clearChatState() {
    try {
        sessionStorage.removeItem(CHAT_STORAGE_KEY);
        sessionStorage.removeItem(CHAT_SESSION_KEY);
        return true;
    } catch (error) {
        console.error('Failed to clear chat state:', error);
        return false;
    }
}

/**
 * Check if there's saved chat state
 * @returns {boolean}
 */
function hasSavedChatState() {
    const { messagesHtml } = loadChatState();
    return messagesHtml !== null && messagesHtml.length > 0;
}

// Export for module usage (if needed in future)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { saveChatState, loadChatState, clearChatState, hasSavedChatState };
}
