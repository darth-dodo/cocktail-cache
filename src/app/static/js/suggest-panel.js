/**
 * Suggest Panel
 * Loads and renders bottle suggestions when the Suggest tab is selected.
 * Fetches recommendations based on the user's cabinet ingredients.
 */
(function() {
    'use strict';

    const CABINET_STORAGE_KEY = 'cocktail-cache-cabinet';
    const API_ENDPOINT = '/api/suggest-bottles';
    const DEFAULT_LIMIT = 10;

    let initialized = false;
    let isLoading = false;
    let lastCabinetHash = '';

    /**
     * Get cabinet ingredients from localStorage
     * @returns {string[]} Array of ingredient IDs
     */
    function getCabinetFromStorage() {
        try {
            const stored = localStorage.getItem(CABINET_STORAGE_KEY);
            if (stored) {
                const parsed = JSON.parse(stored);
                if (Array.isArray(parsed) && parsed.every(item => typeof item === 'string')) {
                    return parsed;
                }
            }
        } catch (error) {
            console.error('SuggestPanel: Failed to load cabinet from localStorage:', error);
        }
        return [];
    }

    /**
     * Create a hash of the cabinet for change detection
     * @param {string[]} cabinet - Array of ingredient IDs
     * @returns {string} Hash string
     */
    function hashCabinet(cabinet) {
        return cabinet.slice().sort().join(',');
    }

    /**
     * Format ingredient name for display
     * @param {string} name - Raw ingredient name
     * @returns {string} Formatted name
     */
    function formatIngredientName(name) {
        if (!name) return '';
        return name
            .replace(/-/g, ' ')
            .replace(/_/g, ' ')
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');
    }

    /**
     * Get emoji for ingredient based on name
     * @param {string} name - Ingredient name
     * @returns {string} Emoji
     */
    function getIngredientEmoji(name) {
        const lowerName = name.toLowerCase();

        // Citrus
        if (lowerName.includes('lime')) return '🍋';
        if (lowerName.includes('lemon')) return '🍋';
        if (lowerName.includes('orange')) return '🍊';
        if (lowerName.includes('grapefruit')) return '🍊';

        // Spirits
        if (lowerName.includes('vodka')) return '🍸';
        if (lowerName.includes('gin')) return '🍸';
        if (lowerName.includes('rum')) return '🥃';
        if (lowerName.includes('whiskey') || lowerName.includes('whisky') || lowerName.includes('bourbon')) return '🥃';
        if (lowerName.includes('tequila')) return '🥃';
        if (lowerName.includes('brandy') || lowerName.includes('cognac')) return '🥃';

        // Liqueurs
        if (lowerName.includes('liqueur') || lowerName.includes('triple sec') || lowerName.includes('curacao')) return '🍾';
        if (lowerName.includes('vermouth')) return '🍷';
        if (lowerName.includes('bitters')) return '🧪';

        // Mixers
        if (lowerName.includes('soda') || lowerName.includes('tonic') || lowerName.includes('cola')) return '🥤';
        if (lowerName.includes('juice')) return '🧃';
        if (lowerName.includes('syrup') || lowerName.includes('sugar')) return '🍯';
        if (lowerName.includes('cream') || lowerName.includes('milk')) return '🥛';

        // Garnishes
        if (lowerName.includes('mint')) return '🌿';
        if (lowerName.includes('cherry')) return '🍒';
        if (lowerName.includes('olive')) return '🫒';

        // Default
        return '🍾';
    }

    /**
     * Format drinks list for "Appears in" text
     * @param {string[]} drinks - Array of drink names
     * @returns {string} Formatted string
     */
    function formatDrinksList(drinks) {
        if (!drinks || drinks.length === 0) return '';

        const displayDrinks = drinks.slice(0, 3);
        const formattedDrinks = displayDrinks.join(', ');

        if (drinks.length > 3) {
            return formattedDrinks + '...';
        }
        return formattedDrinks;
    }

    /**
     * Render the loading state
     */
    function renderLoading() {
        const panel = document.getElementById('panel-suggest');
        if (!panel) return;

        panel.innerHTML = `
            <div class="p-4 flex items-center justify-center min-h-[200px]">
                <div class="text-center">
                    <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500 mb-3"></div>
                    <p class="text-stone-400 text-sm">Finding recommendations...</p>
                </div>
            </div>
        `;
    }

    /**
     * Render the empty state (no cabinet ingredients)
     * @param {number} cabinetCount - Number of ingredients in cabinet
     */
    function renderEmpty(cabinetCount) {
        const panel = document.getElementById('panel-suggest');
        if (!panel) return;

        panel.innerHTML = `
            <div class="p-4 space-y-4">
                <!-- Summary -->
                <div class="glass-card p-4">
                    <div class="flex items-center justify-between">
                        <div>
                            <h2 class="text-lg font-semibold text-amber-200">Grow Your Bar</h2>
                            <p class="text-xs text-stone-400">Based on your <span id="suggest-cabinet-count">${cabinetCount}</span> ingredients</p>
                        </div>
                        <div class="text-right">
                            <div class="text-2xl font-bold text-amber-300" id="suggest-makeable">0</div>
                            <div class="text-xs text-stone-500">drinks you can make</div>
                        </div>
                    </div>
                </div>

                <!-- Empty state -->
                <div id="suggest-empty" class="text-center py-8">
                    <div class="text-4xl mb-2">&#127870;</div>
                    <p class="text-stone-400">Add some ingredients to your cabinet first</p>
                    <button id="suggest-to-cabinet" class="btn btn-sm glass-btn-primary mt-3">
                        Go to Cabinet
                    </button>
                </div>
            </div>
        `;

        // Attach click handler for "Go to Cabinet" button
        const goToCabinetBtn = document.getElementById('suggest-to-cabinet');
        if (goToCabinetBtn) {
            goToCabinetBtn.addEventListener('click', function() {
                if (window.TabManager && typeof window.TabManager.switchTo === 'function') {
                    window.TabManager.switchTo('cabinet');
                }
            });
        }
    }

    /**
     * Render an error state with retry button
     * @param {string} message - Error message
     */
    function renderError(message) {
        const panel = document.getElementById('panel-suggest');
        if (!panel) return;

        panel.innerHTML = `
            <div class="p-4 space-y-4">
                <div class="text-center py-8">
                    <div class="text-4xl mb-2">&#9888;&#65039;</div>
                    <p class="text-stone-400 mb-3">${message || 'Something went wrong'}</p>
                    <button id="suggest-retry" class="btn btn-sm glass-btn-primary">
                        Try Again
                    </button>
                </div>
            </div>
        `;

        // Attach click handler for retry button
        const retryBtn = document.getElementById('suggest-retry');
        if (retryBtn) {
            retryBtn.addEventListener('click', function() {
                refresh();
            });
        }
    }

    /**
     * Render the recommendations
     * @param {Object} data - Response data from API
     * @param {number} cabinetCount - Number of ingredients in cabinet
     */
    function renderRecommendations(data, cabinetCount) {
        const panel = document.getElementById('panel-suggest');
        if (!panel) return;

        const recommendations = data.recommendations || [];
        const makeableCount = data.drinks_makeable_now || 0;

        // Build recommendations HTML
        let recommendationsHtml = '';
        recommendations.forEach(rec => {
            // Handle both old and new API response formats
            const name = rec.ingredient_name || formatIngredientName(rec.ingredient_id || rec.ingredient);
            const ingredientId = rec.ingredient_id || rec.ingredient;
            const emoji = getIngredientEmoji(ingredientId);
            const unlockCount = rec.new_drinks_unlocked || rec.unlocks_count || 0;
            // Extract drink names from drinks array or use unlocks directly
            const drinkNames = rec.drinks ? rec.drinks.map(d => d.name) : (rec.unlocks || []);
            const appearsIn = formatDrinksList(drinkNames);

            recommendationsHtml += `
                <div class="glass-card p-4 hover:border-amber-500/30 transition-all">
                    <div class="flex items-start gap-3">
                        <div class="w-10 h-10 rounded-full bg-amber-900/50 flex items-center justify-center flex-shrink-0">
                            <span class="text-lg">${emoji}</span>
                        </div>
                        <div class="flex-1 min-w-0">
                            <div class="flex items-start justify-between gap-2">
                                <h3 class="text-amber-200 font-medium">${name}</h3>
                                <span class="text-amber-400 font-bold text-sm whitespace-nowrap">+${unlockCount} drinks</span>
                            </div>
                            ${appearsIn ? `<p class="text-stone-500 text-xs mt-1">Appears in: ${appearsIn}</p>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });

        // If no recommendations, show a different message
        if (recommendations.length === 0) {
            recommendationsHtml = `
                <div class="text-center py-6">
                    <div class="text-3xl mb-2">&#127881;</div>
                    <p class="text-stone-400 text-sm">You have a great collection! No additional recommendations at this time.</p>
                </div>
            `;
        }

        panel.innerHTML = `
            <div class="p-4 space-y-4">
                <!-- Summary -->
                <div class="glass-card p-4">
                    <div class="flex items-center justify-between">
                        <div>
                            <h2 class="text-lg font-semibold text-amber-200">Grow Your Bar</h2>
                            <p class="text-xs text-stone-400">Based on your <span id="suggest-cabinet-count">${cabinetCount}</span> ingredients</p>
                        </div>
                        <div class="text-right">
                            <div class="text-2xl font-bold text-amber-300" id="suggest-makeable">${makeableCount}</div>
                            <div class="text-xs text-stone-500">drinks you can make</div>
                        </div>
                    </div>
                </div>

                <!-- Recommendations List -->
                <div id="suggest-list" class="space-y-3">
                    ${recommendationsHtml}
                </div>
            </div>
        `;
    }

    /**
     * Fetch suggestions from the API
     * @param {string[]} cabinet - Array of ingredient IDs
     * @returns {Promise<Object>} API response data
     */
    async function fetchSuggestions(cabinet) {
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                cabinet: cabinet,
                drink_type: 'all',
                limit: DEFAULT_LIMIT
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Load and render suggestions
     * @param {boolean} force - Force reload even if cabinet hasn't changed
     */
    async function loadSuggestions(force = false) {
        if (isLoading) return;

        const cabinet = getCabinetFromStorage();
        const currentHash = hashCabinet(cabinet);

        // Skip if cabinet hasn't changed (unless forced)
        if (!force && currentHash === lastCabinetHash) {
            return;
        }

        // If cabinet is empty, show empty state
        if (cabinet.length === 0) {
            lastCabinetHash = currentHash;
            renderEmpty(0);
            return;
        }

        isLoading = true;
        renderLoading();

        try {
            const data = await fetchSuggestions(cabinet);
            lastCabinetHash = currentHash;
            renderRecommendations(data, cabinet.length);
        } catch (error) {
            console.error('SuggestPanel: Failed to fetch suggestions:', error);
            renderError('Failed to load recommendations. Please try again.');
        } finally {
            isLoading = false;
        }
    }

    /**
     * Handle tab change event
     * @param {CustomEvent} event - Tab changed event
     */
    function handleTabChanged(event) {
        const { tab } = event.detail || {};
        if (tab === 'suggest') {
            loadSuggestions();
        }
    }

    /**
     * Handle cabinet update event
     */
    function handleCabinetUpdated() {
        // If we're currently on the suggest tab, reload
        if (window.TabManager && window.TabManager.getCurrentTab() === 'suggest') {
            loadSuggestions(true);
        } else {
            // Reset the hash so next time we visit suggest tab, it reloads
            lastCabinetHash = '';
        }
    }

    /**
     * Force refresh suggestions
     */
    function refresh() {
        loadSuggestions(true);
    }

    /**
     * Initialize the suggest panel
     */
    function init() {
        if (initialized) {
            console.warn('SuggestPanel: Already initialized');
            return;
        }

        // Listen for tab changes
        window.addEventListener('tab-changed', handleTabChanged);

        // Listen for cabinet updates
        window.addEventListener('cabinet-updated', handleCabinetUpdated);

        initialized = true;

        // If we're already on the suggest tab, load suggestions
        if (window.TabManager && window.TabManager.getCurrentTab() === 'suggest') {
            loadSuggestions();
        }
    }

    // Public API
    window.SuggestPanel = {
        init: init,
        refresh: refresh,
        getCabinetFromStorage: getCabinetFromStorage
    };

    // Auto-initialize on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        // DOM already loaded
        init();
    }
})();
