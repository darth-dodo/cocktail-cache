/**
 * Browse Panel for Cocktail Cache
 *
 * Loads and renders the browse drinks content when the Browse tab is selected.
 * Features search filtering, type filtering, and drink card selection.
 */
(function() {
    'use strict';

    // State
    let drinksCache = null;
    let contentLoaded = false;
    let currentFilter = 'all';
    let searchQuery = '';
    let searchTimeout = null;

    const SEARCH_DEBOUNCE_MS = 150;

    /**
     * Initialize the browse panel
     */
    function init() {
        // Listen for tab changes
        window.addEventListener('tab-changed', handleTabChange);

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
     * Load content into the browse panel
     */
    async function loadContent() {
        const panel = document.getElementById('panel-browse');
        if (!panel) {
            console.warn('BrowsePanel: #panel-browse element not found');
            return;
        }

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
     * Render the main panel content structure
     * @returns {string} HTML string
     */
    function renderPanelContent() {
        return `
            <div class="p-4 space-y-4">
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
                    <div class="flex gap-2">
                        <button class="browse-filter glass-chip px-3 py-1.5 text-xs active" data-filter="all">All</button>
                        <button class="browse-filter glass-chip px-3 py-1.5 text-xs" data-filter="cocktail">Cocktails</button>
                        <button class="browse-filter glass-chip px-3 py-1.5 text-xs" data-filter="mocktail">Mocktails</button>
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
     * Setup event listeners for search and filters
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

            // Handle Enter key
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    searchInput.value = '';
                    searchQuery = '';
                    renderDrinks();
                }
            });
        }

        // Filter buttons
        document.querySelectorAll('.browse-filter').forEach(btn => {
            btn.addEventListener('click', () => {
                // Update active state
                document.querySelectorAll('.browse-filter').forEach(b => {
                    b.classList.remove('active');
                });
                btn.classList.add('active');

                // Update filter and re-render
                currentFilter = btn.dataset.filter;
                renderDrinks();
            });
        });
    }

    /**
     * Filter drinks based on current search query and type filter
     * @returns {Array} Filtered drinks
     */
    function getFilteredDrinks() {
        if (!drinksCache) return [];

        let filtered = [...drinksCache];

        // Apply type filter
        if (currentFilter !== 'all') {
            filtered = filtered.filter(drink => {
                const drinkType = (drink.drink_type || '').toLowerCase();
                return drinkType === currentFilter;
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
     * Render the drinks grid
     */
    function renderDrinks() {
        const grid = document.getElementById('browse-grid');
        const countEl = document.getElementById('browse-count');

        if (!grid) return;

        const filtered = getFilteredDrinks();

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
                    <button onclick="window.BrowsePanel.setFilter('all'); document.getElementById('browse-search').value = '';"
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
                    emitDrinkSelected(drink);
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
                ${displayTags.length > 0 ? `
                    <div class="flex flex-wrap gap-1 mt-2">
                        ${displayTags.map(tag => `
                            <span class="text-[10px] px-1.5 py-0.5 rounded bg-amber-900/30 text-amber-300/70">${escapeHtml(tag)}</span>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Emit drink-selected custom event
     * @param {Object} drink - The selected drink data
     */
    function emitDrinkSelected(drink) {
        const event = new CustomEvent('drink-selected', {
            bubbles: true,
            detail: { drink }
        });
        window.dispatchEvent(event);
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
        currentFilter = 'all';
        searchQuery = '';
        loadContent();
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

        currentFilter = type;

        // Update button states
        document.querySelectorAll('.browse-filter').forEach(btn => {
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
        setFilter: setFilter
    };

    // Auto-initialize on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        // DOM already loaded
        init();
    }
})();
