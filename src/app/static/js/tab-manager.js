/**
 * Tab Manager for Unified Chat Interface
 *
 * Manages tab switching between chat, cabinet, browse, and suggest panels.
 * Emits custom events for tab changes and supports programmatic switching.
 */
(function() {
    'use strict';

    const STORAGE_KEY = 'cocktail-cache-active-tab';
    const DEFAULT_TAB = 'chat';
    const VALID_TABS = ['chat', 'cabinet', 'browse', 'suggest'];

    // CSS classes for tab states
    const ACTIVE_CLASSES = ['text-amber-300', 'border-amber-500'];
    const INACTIVE_CLASSES = ['text-stone-400', 'border-transparent'];

    let currentTab = DEFAULT_TAB;
    let initialized = false;

    /**
     * Get DOM elements for a specific tab
     * @param {string} tabName - Name of the tab
     * @returns {{ button: Element|null, panel: Element|null }}
     */
    function getTabElements(tabName) {
        return {
            button: document.querySelector(`[data-tab="${tabName}"]`),
            panel: document.getElementById(`panel-${tabName}`)
        };
    }

    /**
     * Update tab button styling
     * @param {Element} button - Tab button element
     * @param {boolean} isActive - Whether the tab is active
     */
    function updateTabStyling(button, isActive) {
        if (!button) return;

        if (isActive) {
            INACTIVE_CLASSES.forEach(cls => button.classList.remove(cls));
            ACTIVE_CLASSES.forEach(cls => button.classList.add(cls));
        } else {
            ACTIVE_CLASSES.forEach(cls => button.classList.remove(cls));
            INACTIVE_CLASSES.forEach(cls => button.classList.add(cls));
        }

        // Update ARIA attributes
        button.setAttribute('aria-selected', isActive ? 'true' : 'false');
        button.setAttribute('tabindex', isActive ? '0' : '-1');
    }

    /**
     * Show or hide a panel
     * @param {Element} panel - Panel element
     * @param {boolean} isVisible - Whether the panel should be visible
     */
    function updatePanelVisibility(panel, isVisible) {
        if (!panel) return;

        if (isVisible) {
            panel.classList.remove('hidden');
            panel.setAttribute('aria-hidden', 'false');
        } else {
            panel.classList.add('hidden');
            panel.setAttribute('aria-hidden', 'true');
        }
    }

    /**
     * Emit tab-changed custom event
     * @param {string} newTab - The new active tab
     * @param {string} previousTab - The previously active tab
     */
    function emitTabChanged(newTab, previousTab) {
        const event = new CustomEvent('tab-changed', {
            bubbles: true,
            detail: {
                tab: newTab,
                previousTab: previousTab
            }
        });
        window.dispatchEvent(event);
    }

    /**
     * Save active tab to session storage
     * @param {string} tabName - Name of the tab to save
     */
    function saveActiveTab(tabName) {
        try {
            sessionStorage.setItem(STORAGE_KEY, tabName);
        } catch (e) {
            // Session storage might be unavailable in some contexts
            console.warn('TabManager: Could not save to sessionStorage', e);
        }
    }

    /**
     * Load active tab from session storage
     * @returns {string} The saved tab name or default
     */
    function loadActiveTab() {
        try {
            const saved = sessionStorage.getItem(STORAGE_KEY);
            if (saved && VALID_TABS.includes(saved)) {
                return saved;
            }
        } catch (e) {
            console.warn('TabManager: Could not read from sessionStorage', e);
        }
        return DEFAULT_TAB;
    }

    /**
     * Switch to a specific tab
     * @param {string} tabName - Name of the tab to switch to
     * @param {Object} options - Optional configuration
     * @param {boolean} options.silent - If true, don't emit event
     * @param {boolean} options.save - If true, save to session storage (default: true)
     * @returns {boolean} True if switch was successful
     */
    function switchTo(tabName, options = {}) {
        const { silent = false, save = true } = options;

        // Validate tab name
        if (!VALID_TABS.includes(tabName)) {
            console.error(`TabManager: Invalid tab name "${tabName}". Valid tabs: ${VALID_TABS.join(', ')}`);
            return false;
        }

        // Skip if already on this tab
        if (tabName === currentTab && initialized) {
            return true;
        }

        const previousTab = currentTab;

        // Update all tabs
        VALID_TABS.forEach(tab => {
            const { button, panel } = getTabElements(tab);
            const isActive = tab === tabName;

            updateTabStyling(button, isActive);
            updatePanelVisibility(panel, isActive);
        });

        // Update current state
        currentTab = tabName;

        // Save to session storage
        if (save) {
            saveActiveTab(tabName);
        }

        // Emit event
        if (!silent) {
            emitTabChanged(tabName, previousTab);
        }

        return true;
    }

    /**
     * Get the currently active tab
     * @returns {string} Current tab name
     */
    function getCurrentTab() {
        return currentTab;
    }

    /**
     * Handle tab button click
     * @param {Event} event - Click event
     */
    function handleTabClick(event) {
        const button = event.currentTarget;
        const tabName = button.dataset.tab;

        if (tabName) {
            switchTo(tabName);
        }
    }

    /**
     * Handle keyboard navigation within tabs
     * @param {KeyboardEvent} event - Keyboard event
     */
    function handleTabKeydown(event) {
        const button = event.target;
        if (!button.dataset.tab) return;

        const currentIndex = VALID_TABS.indexOf(button.dataset.tab);
        let newIndex = -1;

        switch (event.key) {
            case 'ArrowLeft':
            case 'ArrowUp':
                newIndex = currentIndex > 0 ? currentIndex - 1 : VALID_TABS.length - 1;
                break;
            case 'ArrowRight':
            case 'ArrowDown':
                newIndex = currentIndex < VALID_TABS.length - 1 ? currentIndex + 1 : 0;
                break;
            case 'Home':
                newIndex = 0;
                break;
            case 'End':
                newIndex = VALID_TABS.length - 1;
                break;
            default:
                return;
        }

        if (newIndex >= 0) {
            event.preventDefault();
            const newTab = VALID_TABS[newIndex];
            const { button: newButton } = getTabElements(newTab);

            if (newButton) {
                newButton.focus();
                switchTo(newTab);
            }
        }
    }

    /**
     * Initialize the tab manager
     */
    function init() {
        if (initialized) {
            console.warn('TabManager: Already initialized');
            return;
        }

        // Find all tab buttons and attach event listeners
        const tabButtons = document.querySelectorAll('[data-tab]');

        if (tabButtons.length === 0) {
            console.warn('TabManager: No tab buttons found. Make sure buttons have data-tab attributes.');
            return;
        }

        tabButtons.forEach(button => {
            button.addEventListener('click', handleTabClick);
            button.addEventListener('keydown', handleTabKeydown);

            // Ensure proper ARIA role
            if (!button.hasAttribute('role')) {
                button.setAttribute('role', 'tab');
            }
        });

        // Find the tab container and set ARIA role
        const tabContainer = tabButtons[0]?.parentElement;
        if (tabContainer && !tabContainer.hasAttribute('role')) {
            tabContainer.setAttribute('role', 'tablist');
        }

        // Load saved tab or use default
        const savedTab = loadActiveTab();

        // Initialize to the saved tab
        switchTo(savedTab, { silent: true, save: false });

        initialized = true;

        // Emit initial tab event after a brief delay to allow other scripts to attach listeners
        setTimeout(() => {
            emitTabChanged(savedTab, null);
        }, 0);
    }

    // Public API
    window.TabManager = {
        switchTo: switchTo,
        getCurrentTab: getCurrentTab,
        init: init,
        VALID_TABS: Object.freeze([...VALID_TABS])
    };

    // Auto-initialize on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        // DOM already loaded
        init();
    }
})();
