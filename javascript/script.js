
function geminiHighlightWord() {
    const handler = (event) => {
        const textarea = event.target;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const text = textarea.value;

        if (start === end) {
            let s = start;
            while (s > 0 && /\w/.test(text[s - 1])) s--;
            let e = start;
            while (e < text.length && /\w/.test(text[e])) e++;
            const word = text.substring(s, e).trim().toLowerCase();
            if (word) highlightMapping(word);
        } else {
            const selectedText = text.substring(start, end).trim().toLowerCase();
            if (selectedText) highlightMapping(selectedText);
        }
    };

    // Use delegation for dynamic elements in new tab
    document.addEventListener('click', (e) => {
        if (e.target.tagName === 'TEXTAREA' && (e.target.closest('#gemini_pos_prompt') || e.target.closest('#gemini_neg_prompt'))) {
            handler(e);
        }
    });
    document.addEventListener('keyup', (e) => {
        if (e.target.tagName === 'TEXTAREA' && (e.target.closest('#gemini_pos_prompt') || e.target.closest('#gemini_neg_prompt'))) {
            handler(e);
        }
    });
}

function highlightMapping(word) {
    const items = document.querySelectorAll('.translation-item');
    let found = false;
    items.forEach(item => {
        const targetWord = item.getAttribute('data-word').toLowerCase();
        if (targetWord === word || word.includes(targetWord) || targetWord.includes(word)) {
            item.style.backgroundColor = '#ffff0033';
            item.style.fontWeight = 'bold';
            if (!found) {
                item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                found = true;
            }
        } else {
            item.style.backgroundColor = 'transparent';
            item.style.fontWeight = 'normal';
        }
    });
}

onUiLoaded(() => {
    geminiHighlightWord();

    // ADetailer-style: Move checkbox into accordion header
    const setupAccordionCheckbox = () => {
        const checkbox = gradioApp().querySelector('#aipi_prompt_settings_checkbox');
        const accordion = gradioApp().querySelector('#aipi_prompt_settings_accordion');

        if (checkbox && accordion) {
            const labelWrap = accordion.querySelector('.label-wrap');
            if (labelWrap) {
                // Get just the checkbox input and its label container
                const checkboxContainer = checkbox.querySelector('label');
                if (checkboxContainer) {
                    // Create a wrapper to hold the checkbox
                    const wrapper = document.createElement('span');
                    wrapper.id = 'aipi_accordion_checkbox_wrapper';
                    wrapper.style.cssText = 'display: inline-flex; align-items: center; margin-right: 8px;';

                    // Clone the checkbox input
                    const input = checkboxContainer.querySelector('input');
                    if (input) {
                        const newInput = input.cloneNode(true);
                        wrapper.appendChild(newInput);

                        // Prevent clicking the checkbox from toggling the accordion
                        newInput.addEventListener('click', (e) => {
                            e.stopPropagation();
                        });

                        // Sync checkbox state
                        newInput.addEventListener('change', () => {
                            input.checked = newInput.checked;
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                        });

                        // Sync from original to cloned
                        input.addEventListener('change', () => {
                            newInput.checked = input.checked;
                        });

                        // Insert at the beginning of labelWrap
                        labelWrap.insertBefore(wrapper, labelWrap.firstChild);

                        // Alignment is now handled via style.css
                        const titleSpan = Array.from(labelWrap.childNodes).find(node => node.nodeType === 3 || node.tagName === 'SPAN' && node.id !== 'aipi_accordion_checkbox_wrapper');
                        if (titleSpan && titleSpan.style) {
                            titleSpan.style.flex = '1';
                        }

                        // Hide the original checkbox row
                        checkbox.closest('.aipi_accordion_header > div:first-child, [class*="form"]')?.style?.setProperty('display', 'none', 'important');
                        // Try to hide parent container of original checkbox
                        const originalRow = checkbox.closest('.aipi_accordion_header');
                        if (originalRow) {
                            // Restructure: move accordion out of the row
                            const parent = originalRow.parentNode;
                            parent.insertBefore(accordion, originalRow);
                            originalRow.style.display = 'none';
                        }
                    }
                }
            }
        }
    };

    // Run after a short delay to ensure DOM is ready
    setTimeout(setupAccordionCheckbox, 500);

    document.addEventListener('click', (e) => {
        const target = e.target;

        // Helper to find the last visited generation tab
        const getPreferredTab = () => {
            // In standalone tab, we can't rely on 'selected' tab to be the target
            // But usually users want txt2img or img2img.
            // For now, let's Stick to checking if they were previously on img2img or default to txt2img.
            // Actually, WebUI doesn't track "last generation tab" easily. 
            // We'll default to txt2img unless the user explicitly switched? 
            // Let's check the current selected tab. If it's AIPI, we default to txt2img.
            const selectedTab = gradioApp().querySelector('#tabs button.selected')?.innerText.toLowerCase() || "";
            if (selectedTab.includes('img2img')) return 'img2img';
            return 'txt2img';
        };

        const transferToSD = (sourceSelector, targetIdSuffix) => {
            const tab = getPreferredTab();
            const source = document.querySelector(`${sourceSelector} textarea`);
            const target = gradioApp().querySelector(`#${tab}${targetIdSuffix} textarea`);
            if (source && target) {
                target.value = source.value;
                target.dispatchEvent(new Event('input', { bubbles: true }));
                // Switch to the target tab
                const tabButton = Array.from(gradioApp().querySelectorAll('#tabs button')).find(b => b.innerText.toLowerCase().includes(tab));
                if (tabButton) tabButton.click();
            }
        };

        if (target.id === 'gemini_pos_send' || target.closest('#gemini_pos_send')) {
            transferToSD('#gemini_pos_prompt', '_prompt');
        }
        else if (target.id === 'gemini_neg_send' || target.closest('#gemini_neg_send')) {
            transferToSD('#gemini_neg_prompt', '_neg_prompt');
        }
        else if (target.id === 'gemini_both_send' || target.closest('#gemini_both_send')) {
            const tab = 'txt2img'; // Explicitly target txt2img as requested

            const posSource = document.querySelector('#gemini_pos_prompt textarea');
            const posTarget = gradioApp().querySelector(`#${tab}_prompt textarea`);
            if (posSource && posTarget) {
                posTarget.value = posSource.value;
                posTarget.dispatchEvent(new Event('input', { bubbles: true }));
            }

            const negSource = document.querySelector('#gemini_neg_prompt textarea');
            const negTarget = gradioApp().querySelector(`#${tab}_neg_prompt textarea`);
            if (negSource && negTarget) {
                negTarget.value = negSource.value;
                negTarget.dispatchEvent(new Event('input', { bubbles: true }));
            }

            const tabButton = Array.from(gradioApp().querySelectorAll('#tabs button')).find(b => b.innerText.toLowerCase() === tab);
            if (tabButton) tabButton.click();
        }
    });
});
