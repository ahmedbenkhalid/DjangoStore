document.addEventListener('DOMContentLoaded', () => {
    const searchWrappers = document.querySelectorAll('.js-search-wrapper');

    searchWrappers.forEach(wrapper => {
        const input = wrapper.querySelector('.js-search-input');
        const clearBtn = wrapper.querySelector('.js-search-clear');
        const dropdown = wrapper.querySelector('.js-search-dropdown');
        const resultsContainer = wrapper.querySelector('.js-search-results');
        const viewAllLink = wrapper.querySelector('.js-search-all');
        const form = wrapper.querySelector('.js-search-form') || wrapper.querySelector('form');

        if (!input) return;

        let debounceTimer;
        let selectedIndex = -1;
        let currentSuggestions = [];

        function closeDropdown() {
            if (dropdown) dropdown.style.display = 'none';
            selectedIndex = -1;
        }

        function openDropdown() {
            if (dropdown && currentSuggestions.length > 0) {
                dropdown.style.display = 'block';
            }
        }

        function renderResults(query, results) {
            currentSuggestions = results;
            if (!dropdown || !resultsContainer) return;

            resultsContainer.innerHTML = '';

            if (results.length === 0) {
                closeDropdown();
                return;
            }

            results.forEach((item, idx) => {
                const a = document.createElement('a');
                a.className = 'dropdown-item py-2 px-3 d-flex align-items-center gap-2 js-search-item';
                a.href = item.url;

                let html = '<div class="flex-grow-1">';
                html += '<div class="fw-medium">' + item.name + '</div>';
                if (item.price) {
                    html += '<small class="text-muted">' + item.price + '</small>';
                }
                html += '</div>';

                if (item.image) {
                    const imgHtml = '<img src="' + item.image + '" class="rounded me-2" style="width: 40px; height: 40px; object-fit: cover;">';
                    html = imgHtml + html;
                }

                a.innerHTML = html;

                a.addEventListener('mouseenter', () => {
                    updateSelection(idx);
                });

                resultsContainer.appendChild(a);
            });

            if (viewAllLink) {
                viewAllLink.href = '/search/?q=' + encodeURIComponent(query);
            }

            openDropdown();
            updateSelection(-1);
        }

        function updateSelection(index) {
            selectedIndex = index;
            if (!resultsContainer) return;
            const items = resultsContainer.querySelectorAll('.js-search-item');
            items.forEach((item, i) => {
                if (i === index) {
                    item.classList.add('bg-light');
                } else {
                    item.classList.remove('bg-light');
                }
            });
        }

        function fetchResults(query) {
            if (query.trim() === '') {
                currentSuggestions = [];
                renderResults(query, []);
                return;
            }


            fetch('/search/?q=' + encodeURIComponent(query), { headers: { 'Accept': 'application/json' } })
                .then(res => {
                    if (res.ok) return res.json();
                    return { results: [] };
                })
                .then(data => {
                    const results = data.results || data || [];
                    renderResults(query, results.slice(0, 5));
                })
                .catch(err => {
                    console.error('Search error:', err);
                });
        }

        input.addEventListener('input', (e) => {
            const val = e.target.value;
            if (clearBtn) {
                if (val.length > 0) clearBtn.classList.remove('d-none');
                else clearBtn.classList.add('d-none');
            }

            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                fetchResults(val);
            }, 300);
        });

        input.addEventListener('focus', () => {
            if (input.value.length > 0 && currentSuggestions.length > 0) {
                openDropdown();
            } else if (input.value.length > 0) {
                fetchResults(input.value);
            }
        });

        input.addEventListener('keydown', (e) => {
            if (!dropdown || dropdown.style.display === 'none') {
                if (e.key === 'Enter') return;
                return;
            }

            const items = resultsContainer.querySelectorAll('.js-search-item');

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                let next = selectedIndex + 1;
                if (next >= items.length) next = 0;
                updateSelection(next);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                let next = selectedIndex - 1;
                if (next < 0) next = items.length - 1;
                updateSelection(next);
            } else if (e.key === 'Enter') {
                if (selectedIndex >= 0 && selectedIndex < items.length) {
                    e.preventDefault();
                    items[selectedIndex].click();
                }
            } else if (e.key === 'Escape') {
                closeDropdown();
                input.blur();
            }
        });

        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                input.value = '';
                clearBtn.classList.add('d-none');
                closeDropdown();
                input.focus();
            });
        }

        document.addEventListener('click', (e) => {
            if (!wrapper.contains(e.target)) {
                closeDropdown();
            }
        });
    });
});
