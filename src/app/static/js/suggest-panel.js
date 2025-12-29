/**
 * Suggest Panel
 * Loads and renders bottle suggestions when the Suggest tab is selected.
 * Fetches recommendations based on the user's cabinet ingredients.
 * Features: Add to Cabinet, Progress indicator, Category grouping
 */
(function() {
    'use strict';

    const CABINET_STORAGE_KEY = 'cocktail-cache-cabinet';
    const API_ENDPOINT = '/api/suggest-bottles';
    const DEFAULT_LIMIT = 10;

    // Category definitions for grouping suggestions
    const CATEGORY_SPIRITS = ['vodka', 'gin', 'rum', 'whiskey', 'whisky', 'bourbon', 'tequila', 'mezcal', 'brandy', 'cognac', 'scotch', 'rye'];
    const CATEGORY_LIQUEURS = ['liqueur', 'triple sec', 'curacao', 'vermouth', 'bitters', 'amaretto', 'kahlua', 'baileys', 'cointreau', 'campari', 'aperol', 'chartreuse', 'benedictine', 'drambuie', 'frangelico', 'galliano', 'grand marnier', 'maraschino', 'midori', 'sambuca', 'schnapps', 'sloe gin', 'st germain', 'absinthe', 'pimms', 'chambord'];

    let initialized = false;
    let isLoading = false;
    let lastCabinetHash = '';

    /**
     * Escape HTML to prevent XSS
     * @param {string} str - String to escape
     * @returns {string} Escaped string
     */
    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

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
     * Save cabinet to localStorage and dispatch event
     * @param {string[]} cabinet - Array of ingredient IDs
     */
    function saveCabinetToStorage(cabinet) {
        try {
            localStorage.setItem(CABINET_STORAGE_KEY, JSON.stringify(cabinet));
            window.dispatchEvent(new CustomEvent('cabinet-updated'));
        } catch (error) {
            console.error('SuggestPanel: Failed to save cabinet to localStorage:', error);
        }
    }

    /**
     * Add ingredient to cabinet
     * @param {string} ingredientId - Ingredient ID to add
     * @returns {boolean} True if added, false if already exists
     */
    function addToCabinet(ingredientId) {
        const cabinet = getCabinetFromStorage();
        if (!cabinet.includes(ingredientId)) {
            cabinet.push(ingredientId);
            saveCabinetToStorage(cabinet);
            return true;
        }
        return false;
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
            .map(word => {
                // Handle apostrophes properly: "lyre's" -> "Lyre's" not "Lyre'S"
                if (word.includes("'")) {
                    const parts = word.split("'");
                    return parts[0].charAt(0).toUpperCase() + parts[0].slice(1).toLowerCase() +
                           "'" + parts.slice(1).join("'").toLowerCase();
                }
                return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
            })
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
        if (lowerName.includes('lime')) return '&#127819;';
        if (lowerName.includes('lemon')) return '&#127819;';
        if (lowerName.includes('orange')) return '&#127818;';
        if (lowerName.includes('grapefruit')) return '&#127818;';

        // Spirits
        if (lowerName.includes('vodka')) return '&#127864;';
        if (lowerName.includes('gin')) return '&#127864;';
        if (lowerName.includes('rum')) return '&#129371;';
        if (lowerName.includes('whiskey') || lowerName.includes('whisky') || lowerName.includes('bourbon')) return '&#129371;';
        if (lowerName.includes('tequila')) return '&#129371;';
        if (lowerName.includes('brandy') || lowerName.includes('cognac')) return '&#129371;';

        // Liqueurs
        if (lowerName.includes('liqueur') || lowerName.includes('triple sec') || lowerName.includes('curacao')) return '&#127870;';
        if (lowerName.includes('vermouth')) return '&#127863;';
        if (lowerName.includes('bitters')) return '&#129514;';

        // Mixers
        if (lowerName.includes('soda') || lowerName.includes('tonic') || lowerName.includes('cola')) return '&#129380;';
        if (lowerName.includes('juice')) return '&#129475;';
        if (lowerName.includes('syrup') || lowerName.includes('sugar')) return '&#127855;';
        if (lowerName.includes('cream') || lowerName.includes('milk')) return '&#129371;';

        // Garnishes
        if (lowerName.includes('mint')) return '&#127807;';
        if (lowerName.includes('cherry')) return '&#127826;';
        if (lowerName.includes('olive')) return '&#129795;';

        // Default
        return '&#127870;';
    }

    /**
     * Categorize an ingredient
     * @param {string} ingredientId - Ingredient ID
     * @returns {string} Category name
     */
    function categorizeIngredient(ingredientId) {
        const lowerName = ingredientId.toLowerCase();

        // Check if it's a spirit
        for (const spirit of CATEGORY_SPIRITS) {
            if (lowerName.includes(spirit)) {
                return 'spirits';
            }
        }

        // Check if it's a liqueur/modifier
        for (const liqueur of CATEGORY_LIQUEURS) {
            if (lowerName.includes(liqueur)) {
                return 'liqueurs';
            }
        }

        // Default to "other"
        return 'other';
    }

    /**
     * Format drinks list for "Appears in" text
     * @param {string[]} drinks - Array of drink names
     * @returns {string} Formatted string
     */
    function formatDrinksList(drinks) {
        if (!drinks || drinks.length === 0) return '';

        const displayDrinks = drinks.slice(0, 3);
        const formattedDrinks = displayDrinks.map(d => escapeHtml(d)).join(', ');

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
                    <p class="text-stone-400 mb-3">${escapeHtml(message) || 'Something went wrong'}</p>
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
     * Render the progress indicator
     * @param {number} makeableNow - Number of drinks currently makeable
     * @param {Object} topRecommendation - Top recommendation with potential unlocks
     * @returns {string} HTML for progress indicator
     */
    function renderProgressIndicator(makeableNow, topRecommendation) {
        if (!topRecommendation) {
            return `
                <div class="glass-card p-4">
                    <div class="flex items-center gap-3">
                        <div class="text-2xl">&#127881;</div>
                        <div>
                            <p class="text-amber-200 font-medium">Great collection!</p>
                            <p class="text-stone-400 text-sm">You can make <span class="text-amber-300 font-bold">${makeableNow}</span> drinks</p>
                        </div>
                    </div>
                </div>
            `;
        }

        const potentialTotal = makeableNow + topRecommendation.new_drinks_unlocked;
        const currentPercent = potentialTotal > 0 ? Math.round((makeableNow / potentialTotal) * 100) : 0;
        const ingredientName = escapeHtml(topRecommendation.ingredient_name || formatIngredientName(topRecommendation.ingredient_id));

        return `
            <div class="glass-card p-4 space-y-3">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-amber-200 font-medium">Your Progress</p>
                        <p class="text-stone-400 text-xs">Add bottles to unlock more drinks</p>
                    </div>
                    <div class="text-right">
                        <span class="text-2xl font-bold text-amber-300">${makeableNow}</span>
                        <span class="text-stone-500 text-sm">drinks</span>
                    </div>
                </div>

                <!-- Progress Bar -->
                <div class="relative">
                    <div class="h-2 bg-stone-800 rounded-full overflow-hidden">
                        <div class="h-full bg-gradient-to-r from-amber-600 to-amber-400 rounded-full transition-all duration-500"
                             style="width: ${currentPercent}%"></div>
                    </div>
                    <div class="mt-2 flex items-center gap-2">
                        <span class="text-amber-400 text-lg">&#128161;</span>
                        <p class="text-stone-300 text-sm">
                            Add <span class="text-amber-300 font-medium">${ingredientName}</span> to unlock
                            <span class="text-amber-400 font-bold">+${topRecommendation.new_drinks_unlocked}</span> more!
                        </p>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render a single suggestion card
     * @param {Object} rec - Recommendation object
     * @returns {string} HTML for suggestion card
     */
    function renderSuggestionCard(rec) {
        const name = escapeHtml(rec.ingredient_name || formatIngredientName(rec.ingredient_id || rec.ingredient));
        const ingredientId = rec.ingredient_id || rec.ingredient;
        const emoji = getIngredientEmoji(ingredientId);
        const unlockCount = rec.new_drinks_unlocked || rec.unlocks_count || 0;
        const drinkNames = rec.drinks ? rec.drinks.map(d => d.name) : (rec.unlocks || []);
        const appearsIn = formatDrinksList(drinkNames);

        return `
            <div class="glass-card p-4 hover:border-amber-500/30 transition-all suggestion-card" data-ingredient-id="${escapeHtml(ingredientId)}">
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

                        <!-- Add to Cabinet Button -->
                        <button class="add-to-cabinet-btn btn btn-sm glass-btn-secondary mt-3 w-full gap-2"
                                data-ingredient-id="${escapeHtml(ingredientId)}"
                                data-ingredient-name="${name}">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                            </svg>
                            <span class="btn-text">Add to Cabinet</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render a category section with collapsible header
     * @param {string} categoryId - Category identifier
     * @param {string} categoryName - Display name
     * @param {string} categoryEmoji - Emoji for category
     * @param {Object[]} recommendations - Recommendations in this category
     * @param {boolean} isOpen - Whether section starts open
     * @returns {string} HTML for category section
     */
    function renderCategorySection(categoryId, categoryName, categoryEmoji, recommendations, isOpen) {
        if (recommendations.length === 0) return '';

        const cardsHtml = recommendations.map(rec => renderSuggestionCard(rec)).join('');

        return `
            <div class="category-section" data-category="${categoryId}">
                <button type="button" class="category-header w-full text-left flex items-center justify-between py-2 px-3 rounded-lg hover:bg-amber-900/20 transition-colors">
                    <div class="flex items-center gap-2">
                        <span class="text-lg">${categoryEmoji}</span>
                        <span class="text-stone-200 font-medium">${escapeHtml(categoryName)}</span>
                        <span class="text-stone-500 text-xs">(${recommendations.length})</span>
                    </div>
                    <svg class="w-4 h-4 text-stone-500 transform transition-transform category-chevron ${isOpen ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                    </svg>
                </button>
                <div class="category-cards space-y-3 mt-2 ${isOpen ? '' : 'hidden'}">
                    ${cardsHtml}
                </div>
            </div>
        `;
    }

    /**
     * Handle Add to Cabinet button click
     * @param {Event} event - Click event
     */
    function handleAddToCabinet(event) {
        const button = event.currentTarget;
        const ingredientId = button.dataset.ingredientId;
        const ingredientName = button.dataset.ingredientName;

        if (!ingredientId) return;

        const added = addToCabinet(ingredientId);

        if (added) {
            // Visual feedback
            const btnText = button.querySelector('.btn-text');
            const originalText = btnText.textContent;
            btnText.textContent = 'Added!';
            button.classList.remove('glass-btn-secondary');
            button.classList.add('glass-btn-success');
            button.disabled = true;

            // Reset and refresh after delay
            setTimeout(() => {
                btnText.textContent = originalText;
                button.classList.remove('glass-btn-success');
                button.classList.add('glass-btn-secondary');
                button.disabled = false;

                // Refresh suggestions to reflect new cabinet
                refresh();
            }, 1000);
        }
    }

    /**
     * Initialize category toggle handlers
     */
    function initCategoryToggles() {
        const headers = document.querySelectorAll('.category-header');
        headers.forEach(header => {
            header.addEventListener('click', function() {
                const section = this.closest('.category-section');
                const cards = section.querySelector('.category-cards');
                const chevron = this.querySelector('.category-chevron');

                cards.classList.toggle('hidden');
                chevron.classList.toggle('rotate-180');
            });
        });
    }

    /**
     * Initialize Add to Cabinet button handlers
     */
    function initAddToCabinetButtons() {
        const buttons = document.querySelectorAll('.add-to-cabinet-btn');
        buttons.forEach(button => {
            button.addEventListener('click', handleAddToCabinet);
        });
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

        // If no recommendations, show completion message
        if (recommendations.length === 0) {
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

                    <div class="text-center py-6">
                        <div class="text-3xl mb-2">&#127881;</div>
                        <p class="text-stone-400 text-sm">You have a great collection! No additional recommendations at this time.</p>
                    </div>
                </div>
            `;
            return;
        }

        // Group recommendations by category
        const spirits = [];
        const liqueurs = [];
        const other = [];

        recommendations.forEach(rec => {
            const ingredientId = rec.ingredient_id || rec.ingredient;
            const category = categorizeIngredient(ingredientId);

            if (category === 'spirits') {
                spirits.push(rec);
            } else if (category === 'liqueurs') {
                liqueurs.push(rec);
            } else {
                other.push(rec);
            }
        });

        // Build category sections HTML
        const topRecommendation = recommendations[0];
        const progressHtml = renderProgressIndicator(makeableCount, topRecommendation);

        let categoriesHtml = '';
        categoriesHtml += renderCategorySection('spirits', 'Spirits', '&#129371;', spirits, true);
        categoriesHtml += renderCategorySection('liqueurs', 'Liqueurs & Modifiers', '&#127870;', liqueurs, spirits.length === 0);
        categoriesHtml += renderCategorySection('other', 'Other Ingredients', '&#129378;', other, spirits.length === 0 && liqueurs.length === 0);

        panel.innerHTML = `
            <div class="p-4 space-y-4">
                <!-- Summary Header -->
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

                <!-- Progress Indicator -->
                ${progressHtml}

                <!-- Category Sections -->
                <div id="suggest-categories" class="space-y-4">
                    ${categoriesHtml}
                </div>
            </div>
        `;

        // Initialize interactive elements
        initCategoryToggles();
        initAddToCabinetButtons();
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
