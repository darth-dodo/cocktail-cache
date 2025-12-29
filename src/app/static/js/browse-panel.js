/**
 * Browse Panel for Cocktail Cache
 *
 * Loads and renders the browse drinks content when the Browse tab is selected.
 * Features search filtering, type filtering, difficulty filtering, sorting,
 * cabinet match calculation, and drink card selection.
 */
(function() {
    'use strict';

    // State
    let drinksCache = null;
    let contentLoaded = false;
    let currentTypeFilter = 'all';
    let currentDifficultyFilters = new Set(); // Multi-select: 'easy', 'medium', 'hard'
    let currentSort = 'name-asc'; // 'name-asc', 'name-desc', 'difficulty-asc', 'difficulty-desc'
    let searchQuery = '';
    let searchTimeout = null;
    let cabinetIngredients = new Set(); // Ingredient IDs from cabinet
    let showCanMakeOnly = false; // Filter to show only drinks user can make

    const SEARCH_DEBOUNCE_MS = 150;
    const CABINET_STORAGE_KEY = 'cocktail-cache-cabinet';
    const DIFFICULTY_ORDER = { 'easy': 1, 'medium': 2, 'hard': 3 };

    /**
     * Initialize the browse panel
     */
    function init() {
        // Listen for tab changes
        window.addEventListener('tab-changed', handleTabChange);

        // Listen for cabinet updates to recalculate matches
        window.addEventListener('cabinet-updated', handleCabinetUpdate);

        // Check if browse tab is already active on load
        if (window.TabManager && window.TabManager.getCurrentTab() === 'browse') {
            loadContent();
        }
    }

    /**
     * Handle tab change events
     * @param {CustomEvent} event - The tab-changed event
     */
    function handleTabChange(event) {
        if (event.detail && event.detail.tab === 'browse') {
            loadContent();
        }
    }

    /**
     * Handle cabinet update events
     */
    function handleCabinetUpdate() {
        loadCabinetIngredients();
        if (contentLoaded) {
            updateCanMakeSection();
            renderDrinks();
        }
    }

    /**
     * Load cabinet ingredients from localStorage
     */
    function loadCabinetIngredients() {
        cabinetIngredients.clear();
        try {
            const stored = localStorage.getItem(CABINET_STORAGE_KEY);
            if (stored) {
                const cabinet = JSON.parse(stored);
                // Cabinet can be an array of ingredient IDs or objects with id property
                if (Array.isArray(cabinet)) {
                    cabinet.forEach(item => {
                        if (typeof item === 'string') {
                            cabinetIngredients.add(item);
                        } else if (item && item.id) {
                            cabinetIngredients.add(item.id);
                        }
                    });
                }
            }
        } catch (e) {
            console.warn('BrowsePanel: Failed to load cabinet from localStorage', e);
        }
    }

    /**
     * Load content into the browse panel
     */
    async function loadContent() {
        const panel = document.getElementById('panel-browse');
        if (!panel) {
            console.warn('BrowsePanel: #panel-browse element not found');
            return;
        }

        // Load cabinet ingredients
        loadCabinetIngredients();

        // Only load once unless refresh is called
        if (contentLoaded && drinksCache) {
            return;
        }

        // Show loading state
        panel.innerHTML = renderLoadingState();

        try {
            // Fetch drinks if not cached
            if (!drinksCache) {
                const response = await fetch('/api/drinks');
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                const data = await response.json();
                drinksCache = data.drinks || [];
            }

            // Render the full UI
            panel.innerHTML = renderPanelContent();
            contentLoaded = true;

            // Setup event listeners
            setupEventListeners();

            // Initial render of drinks
            renderDrinks();

        } catch (error) {
            console.error('BrowsePanel: Failed to load drinks', error);
            panel.innerHTML = renderErrorState();
        }
    }

    /**
     * Render loading spinner state
     * @returns {string} HTML string
     */
    function renderLoadingState() {
        return `
            <div class="flex flex-col items-center justify-center py-12 space-y-4">
                <div class="w-10 h-10 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin"></div>
                <p class="text-stone-400 text-sm">Loading drinks...</p>
            </div>
        `;
    }

    /**
     * Render error state
     * @returns {string} HTML string
     */
    function renderErrorState() {
        return `
            <div class="flex flex-col items-center justify-center py-12 space-y-4">
                <div class="w-12 h-12 rounded-full bg-red-900/30 flex items-center justify-center">
                    <svg class="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                    </svg>
                </div>
                <p class="text-stone-400 text-sm">Failed to load drinks</p>
                <button onclick="window.BrowsePanel.refresh()" class="btn btn-sm glass-btn-secondary">
                    Try Again
                </button>
            </div>
        `;
    }

    /**
     * Get drinks that user can make (100% ingredient match)
     * @returns {Array} Drinks user can make
     */
    function getCanMakeDrinks() {
        if (!drinksCache) return [];

        return drinksCache.filter(drink => {
            const match = calculateCabinetMatch(drink);
            return match.total > 0 && match.percentage === 100;
        });
    }

    /**
     * Render the main panel content structure
     * @returns {string} HTML string
     */
    function renderPanelContent() {
        const canMakeDrinks = getCanMakeDrinks();
        const canMakeCount = canMakeDrinks.length;

        return `
            <div class="p-4 space-y-4">
                <!-- I Can Make Section -->
                <div id="can-make-section" class="glass-card p-3 ${canMakeCount === 0 ? 'hidden' : ''}">
                    <div class="flex items-center justify-between mb-2">
                        <div class="flex items-center gap-2">
                            <span class="text-lg">✨</span>
                            <h3 class="text-amber-200 font-medium text-sm">I Can Make</h3>
                            <span class="bg-green-900/50 text-green-400 text-xs px-2 py-0.5 rounded-full" id="can-make-count">${canMakeCount}</span>
                        </div>
                        <button id="toggle-can-make" class="text-xs text-amber-400 hover:text-amber-300 transition-colors">
                            ${showCanMakeOnly ? 'Show All' : 'Show Only'}
                        </button>
                    </div>
                    <div id="can-make-preview" class="flex flex-wrap gap-2 ${showCanMakeOnly ? 'hidden' : ''}">
                        <!-- Preview chips rendered dynamically -->
                    </div>
                </div>

                <!-- Search and Filters -->
                <div class="space-y-3">
                    <div class="relative">
                        <input type="text" id="browse-search"
                               class="glass-input w-full text-sm py-2.5 pl-9"
                               placeholder="Search drinks..."
                               autocomplete="off">
                        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                        </svg>
                    </div>

                    <!-- Type filters -->
                    <div class="flex flex-wrap gap-2">
                        <button class="browse-type-filter glass-chip px-3 py-1.5 text-xs rounded-full active" data-filter="all">All</button>
                        <button class="browse-type-filter glass-chip px-3 py-1.5 text-xs rounded-full" data-filter="cocktail">Cocktails</button>
                        <button class="browse-type-filter glass-chip px-3 py-1.5 text-xs rounded-full" data-filter="mocktail">Mocktails</button>
                    </div>

                    <!-- Difficulty filters (multi-select) -->
                    <div class="flex flex-wrap items-center gap-2">
                        <span class="text-stone-500 text-xs">Difficulty:</span>
                        <button class="browse-difficulty-filter glass-chip px-3 py-1.5 text-xs rounded-full" data-difficulty="easy">Easy</button>
                        <button class="browse-difficulty-filter glass-chip px-3 py-1.5 text-xs rounded-full" data-difficulty="medium">Medium</button>
                        <button class="browse-difficulty-filter glass-chip px-3 py-1.5 text-xs rounded-full" data-difficulty="hard">Hard</button>
                    </div>

                    <!-- Sort options -->
                    <div class="flex items-center gap-2">
                        <span class="text-stone-500 text-xs">Sort:</span>
                        <select id="browse-sort" class="glass-select text-xs py-1.5 px-2 rounded">
                            <option value="name-asc">Name (A-Z)</option>
                            <option value="name-desc">Name (Z-A)</option>
                            <option value="difficulty-asc">Difficulty (Easy first)</option>
                            <option value="difficulty-desc">Difficulty (Hard first)</option>
                        </select>
                    </div>
                </div>

                <!-- Results count -->
                <div id="browse-count" class="text-stone-400 text-xs">${drinksCache.length} drinks</div>

                <!-- Drinks Grid -->
                <div id="browse-grid" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <!-- Drink cards rendered here -->
                </div>
            </div>
        `;
    }

    /**
     * Setup event listeners for search, filters, and sorting
     */
    function setupEventListeners() {
        // Search input with debounce
        const searchInput = document.getElementById('browse-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.trim();

                // Clear previous timeout
                if (searchTimeout) {
                    clearTimeout(searchTimeout);
                }

                // Debounce the search
                searchTimeout = setTimeout(() => {
                    searchQuery = query;
                    renderDrinks();
                }, SEARCH_DEBOUNCE_MS);
            });

            // Handle Escape key
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    searchInput.value = '';
                    searchQuery = '';
                    renderDrinks();
                }
            });
        }

        // Type filter buttons (single select)
        document.querySelectorAll('.browse-type-filter').forEach(btn => {
            btn.addEventListener('click', () => {
                // Update active state
                document.querySelectorAll('.browse-type-filter').forEach(b => {
                    b.classList.remove('active');
                });
                btn.classList.add('active');

                // Update filter and re-render
                currentTypeFilter = btn.dataset.filter;
                renderDrinks();
            });
        });

        // Difficulty filter buttons (multi-select)
        document.querySelectorAll('.browse-difficulty-filter').forEach(btn => {
            btn.addEventListener('click', () => {
                const difficulty = btn.dataset.difficulty;

                // Toggle selection
                if (currentDifficultyFilters.has(difficulty)) {
                    currentDifficultyFilters.delete(difficulty);
                    btn.classList.remove('active');
                } else {
                    currentDifficultyFilters.add(difficulty);
                    btn.classList.add('active');
                }

                renderDrinks();
            });
        });

        // Sort dropdown
        const sortSelect = document.getElementById('browse-sort');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                currentSort = e.target.value;
                renderDrinks();
            });
        }

        // Toggle "I Can Make" filter
        const toggleCanMake = document.getElementById('toggle-can-make');
        if (toggleCanMake) {
            toggleCanMake.addEventListener('click', () => {
                showCanMakeOnly = !showCanMakeOnly;
                toggleCanMake.textContent = showCanMakeOnly ? 'Show All' : 'Show Only';

                // Toggle preview visibility
                const preview = document.getElementById('can-make-preview');
                if (preview) {
                    preview.classList.toggle('hidden', showCanMakeOnly);
                }

                renderDrinks();
            });
        }

        // Render the "I Can Make" preview chips
        renderCanMakePreview();
    }

    /**
     * Render the "I Can Make" preview chips
     */
    function renderCanMakePreview() {
        const preview = document.getElementById('can-make-preview');
        if (!preview) return;

        const canMakeDrinks = getCanMakeDrinks();

        if (canMakeDrinks.length === 0) {
            preview.innerHTML = '<p class="text-stone-500 text-xs">Add ingredients to your cabinet to see drinks you can make</p>';
            return;
        }

        // Show up to 6 drink chips
        const displayDrinks = canMakeDrinks.slice(0, 6);
        const remaining = canMakeDrinks.length - displayDrinks.length;

        preview.innerHTML = displayDrinks.map(drink => `
            <button class="can-make-chip glass-chip px-2.5 py-1 text-xs rounded-full hover:bg-amber-900/40 transition-colors flex items-center gap-1.5"
                    data-drink-id="${escapeHtml(drink.id)}">
                <span class="text-green-400">✓</span>
                <span class="text-stone-200">${escapeHtml(drink.name)}</span>
            </button>
        `).join('') + (remaining > 0 ? `<span class="text-stone-500 text-xs self-center">+${remaining} more</span>` : '');

        // Add click handlers to chips
        preview.querySelectorAll('.can-make-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const drinkId = chip.dataset.drinkId;
                const drink = drinksCache.find(d => d.id === drinkId);
                if (drink) {
                    navigateToDrink(drink);
                }
            });
        });
    }

    /**
     * Update the "I Can Make" section when cabinet changes
     */
    function updateCanMakeSection() {
        const section = document.getElementById('can-make-section');
        const countEl = document.getElementById('can-make-count');

        const canMakeDrinks = getCanMakeDrinks();
        const count = canMakeDrinks.length;

        if (section) {
            section.classList.toggle('hidden', count === 0);
        }

        if (countEl) {
            countEl.textContent = count;
        }

        renderCanMakePreview();
    }

    /**
     * Calculate cabinet match for a drink
     * @param {Object} drink - Drink data with ingredient_ids array
     * @returns {Object} { matched: number, total: number, percentage: number }
     */
    function calculateCabinetMatch(drink) {
        const ingredientIds = drink.ingredient_ids || [];
        const total = ingredientIds.length;

        if (total === 0) {
            return { matched: 0, total: 0, percentage: 0 };
        }

        let matched = 0;
        ingredientIds.forEach(id => {
            if (id && cabinetIngredients.has(id)) {
                matched++;
            }
        });

        const percentage = Math.round((matched / total) * 100);
        return { matched, total, percentage };
    }

    /**
     * Filter drinks based on current search query, type filter, and difficulty filters
     * @returns {Array} Filtered drinks
     */
    function getFilteredDrinks() {
        if (!drinksCache) return [];

        let filtered = [...drinksCache];

        // Apply "I Can Make" filter
        if (showCanMakeOnly) {
            filtered = filtered.filter(drink => {
                const match = calculateCabinetMatch(drink);
                return match.total > 0 && match.percentage === 100;
            });
        }

        // Apply type filter (cocktail/mocktail based on is_mocktail boolean)
        if (currentTypeFilter !== 'all') {
            filtered = filtered.filter(drink => {
                const isMocktail = drink.is_mocktail === true;
                if (currentTypeFilter === 'mocktail') {
                    return isMocktail;
                } else if (currentTypeFilter === 'cocktail') {
                    return !isMocktail;
                }
                return true;
            });
        }

        // Apply difficulty filters (if any selected, show only those difficulties)
        if (currentDifficultyFilters.size > 0) {
            filtered = filtered.filter(drink => {
                const difficulty = (drink.difficulty || 'easy').toLowerCase();
                return currentDifficultyFilters.has(difficulty);
            });
        }

        // Apply search filter
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            filtered = filtered.filter(drink => {
                const name = (drink.name || '').toLowerCase();
                const tagline = (drink.tagline || '').toLowerCase();
                const tags = (drink.tags || []).map(t => t.toLowerCase()).join(' ');

                return name.includes(query) ||
                       tagline.includes(query) ||
                       tags.includes(query);
            });
        }

        return filtered;
    }

    /**
     * Sort drinks based on current sort option
     * @param {Array} drinks - Array of drinks to sort
     * @returns {Array} Sorted drinks
     */
    function sortDrinks(drinks) {
        const sorted = [...drinks];

        switch (currentSort) {
            case 'name-asc':
                sorted.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
                break;
            case 'name-desc':
                sorted.sort((a, b) => (b.name || '').localeCompare(a.name || ''));
                break;
            case 'difficulty-asc':
                sorted.sort((a, b) => {
                    const diffA = DIFFICULTY_ORDER[(a.difficulty || 'easy').toLowerCase()] || 1;
                    const diffB = DIFFICULTY_ORDER[(b.difficulty || 'easy').toLowerCase()] || 1;
                    if (diffA !== diffB) return diffA - diffB;
                    return (a.name || '').localeCompare(b.name || '');
                });
                break;
            case 'difficulty-desc':
                sorted.sort((a, b) => {
                    const diffA = DIFFICULTY_ORDER[(a.difficulty || 'easy').toLowerCase()] || 1;
                    const diffB = DIFFICULTY_ORDER[(b.difficulty || 'easy').toLowerCase()] || 1;
                    if (diffA !== diffB) return diffB - diffA;
                    return (a.name || '').localeCompare(b.name || '');
                });
                break;
        }

        return sorted;
    }

    /**
     * Render the drinks grid
     */
    function renderDrinks() {
        const grid = document.getElementById('browse-grid');
        const countEl = document.getElementById('browse-count');

        if (!grid) return;

        let filtered = getFilteredDrinks();
        filtered = sortDrinks(filtered);

        // Update count
        if (countEl) {
            const total = drinksCache ? drinksCache.length : 0;
            if (filtered.length === total) {
                countEl.textContent = `${total} drinks`;
            } else {
                countEl.textContent = `${filtered.length} of ${total} drinks`;
            }
        }

        // Render cards or empty state
        if (filtered.length === 0) {
            grid.innerHTML = `
                <div class="col-span-full text-center py-8">
                    <p class="text-stone-500 text-sm">No drinks found</p>
                    <button onclick="window.BrowsePanel.clearFilters();"
                            class="text-amber-400 text-xs mt-2 hover:underline">
                        Clear filters
                    </button>
                </div>
            `;
            return;
        }

        grid.innerHTML = filtered.map(drink => renderDrinkCard(drink)).join('');

        // Add click handlers to cards
        grid.querySelectorAll('[data-drink-id]').forEach(card => {
            card.addEventListener('click', () => {
                const drinkId = card.dataset.drinkId;
                const drink = drinksCache.find(d => d.id === drinkId);
                if (drink) {
                    navigateToDrink(drink);
                }
            });
        });
    }

    /**
     * Render a single drink card
     * @param {Object} drink - Drink data
     * @returns {string} HTML string
     */
    function renderDrinkCard(drink) {
        const tags = drink.tags || [];
        const displayTags = tags.slice(0, 3);
        const difficulty = drink.difficulty || 'Easy';
        const match = calculateCabinetMatch(drink);

        // Determine match badge color based on percentage
        let matchBadgeClass = 'bg-stone-800/50 text-stone-400';
        if (match.total > 0) {
            if (match.percentage >= 80) {
                matchBadgeClass = 'bg-green-900/50 text-green-400';
            } else if (match.percentage >= 50) {
                matchBadgeClass = 'bg-amber-900/50 text-amber-400';
            } else if (match.percentage > 0) {
                matchBadgeClass = 'bg-orange-900/50 text-orange-400';
            }
        }

        return `
            <div class="glass-card p-3 hover:border-amber-500/30 cursor-pointer transition-all" data-drink-id="${escapeHtml(drink.id)}">
                <div class="flex items-start justify-between gap-2">
                    <div class="min-w-0 flex-1">
                        <h3 class="text-amber-200 font-medium text-sm truncate">${escapeHtml(drink.name)}</h3>
                        <p class="text-stone-400 text-xs line-clamp-1">${escapeHtml(drink.tagline || '')}</p>
                    </div>
                    <span class="text-xs px-2 py-0.5 rounded-full bg-stone-800/50 text-stone-400 flex-shrink-0">
                        ${escapeHtml(difficulty)}
                    </span>
                </div>
                <div class="flex items-center justify-between mt-2">
                    ${displayTags.length > 0 ? `
                        <div class="flex flex-wrap gap-1">
                            ${displayTags.map(tag => `
                                <span class="text-[10px] px-1.5 py-0.5 rounded bg-amber-900/30 text-amber-300/70">${escapeHtml(tag)}</span>
                            `).join('')}
                        </div>
                    ` : '<div></div>'}
                    ${match.total > 0 ? `
                        <span class="text-[10px] px-1.5 py-0.5 rounded ${matchBadgeClass} flex-shrink-0 ml-2" title="Ingredients you have">
                            ${match.matched}/${match.total}
                        </span>
                    ` : ''}
                </div>
            </div>
        `;
    }

    /**
     * Navigate to drink detail page
     * @param {Object} drink - The selected drink data
     */
    function navigateToDrink(drink) {
        if (drink && drink.id) {
            window.location.href = `/drink/${encodeURIComponent(drink.id)}`;
        }
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} str - String to escape
     * @returns {string} Escaped string
     */
    function escapeHtml(str) {
        if (typeof str !== 'string') return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    /**
     * Force refresh the drinks data and re-render
     */
    function refresh() {
        drinksCache = null;
        contentLoaded = false;
        currentTypeFilter = 'all';
        currentDifficultyFilters.clear();
        currentSort = 'name-asc';
        searchQuery = '';
        loadContent();
    }

    /**
     * Clear all filters and search
     */
    function clearFilters() {
        // Reset state
        currentTypeFilter = 'all';
        currentDifficultyFilters.clear();
        searchQuery = '';
        showCanMakeOnly = false;

        // Reset UI
        const searchInput = document.getElementById('browse-search');
        if (searchInput) {
            searchInput.value = '';
        }

        // Reset type filter buttons
        document.querySelectorAll('.browse-type-filter').forEach(btn => {
            if (btn.dataset.filter === 'all') {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Reset difficulty filter buttons
        document.querySelectorAll('.browse-difficulty-filter').forEach(btn => {
            btn.classList.remove('active');
        });

        // Reset "I Can Make" toggle
        const toggleCanMake = document.getElementById('toggle-can-make');
        if (toggleCanMake) {
            toggleCanMake.textContent = 'Show Only';
        }
        const preview = document.getElementById('can-make-preview');
        if (preview) {
            preview.classList.remove('hidden');
        }

        renderDrinks();
    }

    /**
     * Programmatically set the type filter
     * @param {string} type - Filter type: 'all', 'cocktail', or 'mocktail'
     */
    function setFilter(type) {
        if (!['all', 'cocktail', 'mocktail'].includes(type)) {
            console.warn('BrowsePanel: Invalid filter type:', type);
            return;
        }

        currentTypeFilter = type;

        // Update button states
        document.querySelectorAll('.browse-type-filter').forEach(btn => {
            if (btn.dataset.filter === type) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        renderDrinks();
    }

    // Public API
    window.BrowsePanel = {
        init: init,
        refresh: refresh,
        setFilter: setFilter,
        clearFilters: clearFilters
    };

    // Auto-initialize on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        // DOM already loaded
        init();
    }
})();
