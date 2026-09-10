        (function () {
            const html = document.documentElement;

            // --- Theme Toggle ---
            const toggleCheckbox = document.getElementById('themeToggleCheckbox');
            const sliderCircle = document.querySelector('.slider-circle');

            function updateThemeUI(theme) {
                if (toggleCheckbox) {
                    toggleCheckbox.checked = (theme === 'dark');
                    if (theme === 'dark') {
                        sliderCircle.style.transform = 'translateX(22px)';
                        sliderCircle.style.backgroundColor = 'var(--accent-primary)';
                    } else {
                        sliderCircle.style.transform = 'translateX(0)';
                        sliderCircle.style.backgroundColor = 'var(--text-muted)';
                    }
                }
            }

            const storedTheme = localStorage.getItem('ml-theme');
            if (storedTheme) {
                html.setAttribute('data-theme', storedTheme);
                updateThemeUI(storedTheme);
            } else {
                updateThemeUI(html.getAttribute('data-theme') || 'dark');
            }

            if (toggleCheckbox) {
                toggleCheckbox.addEventListener('change', function () {
                    const next = this.checked ? 'dark' : 'light';
                    html.setAttribute('data-theme', next);
                    localStorage.setItem('ml-theme', next);
                    updateThemeUI(next);
                });
            }

            // --- Accent Color ---
            const PRESET_COLORS = [
                { name: 'Arancione', hex: '#ea580c' },
                { name: 'Viola', hex: '#7c3aed' },
                { name: 'Blu', hex: '#2563eb' },
                { name: 'Verde', hex: '#16a34a' },
                { name: 'Rosso', hex: '#dc2626' },
                { name: 'Teal', hex: '#0d9488' },
                { name: 'Rosa', hex: '#db2777' },
                { name: 'Giallo', hex: '#ca8a04' },
            ];

            function hexToRgb(hex) {
                hex = hex.replace('#', '');
                if (hex.length === 3) hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
                const r = parseInt(hex.substring(0, 2), 16);
                const g = parseInt(hex.substring(2, 4), 16);
                const b = parseInt(hex.substring(4, 6), 16);
                return { r, g, b };
            }

            function lighten(hex, amount) {
                const { r, g, b } = hexToRgb(hex);
                const lr = Math.min(255, r + amount);
                const lg = Math.min(255, g + amount);
                const lb = Math.min(255, b + amount);
                return `#${lr.toString(16).padStart(2, '0')}${lg.toString(16).padStart(2, '0')}${lb.toString(16).padStart(2, '0')}`;
            }

            function darken(hex, amount) {
                const { r, g, b } = hexToRgb(hex);
                const dr = Math.max(0, r - amount);
                const dg = Math.max(0, g - amount);
                const db = Math.max(0, b - amount);
                return `#${dr.toString(16).padStart(2, '0')}${dg.toString(16).padStart(2, '0')}${db.toString(16).padStart(2, '0')}`;
            }

            function applyAccentColor(hex) {
                const { r, g, b } = hexToRgb(hex);
                const secondary = lighten(hex, 40);
                const darkened = darken(hex, 30);
                const gradient = `linear-gradient(135deg, ${hex} 0%, ${secondary} 50%, ${lighten(hex, 80)} 100%)`;
                const gradientHover = `linear-gradient(135deg, ${darkened} 0%, ${hex} 50%, ${lighten(hex, 60)} 100%)`;

                html.style.setProperty('--accent-primary', hex);
                html.style.setProperty('--accent-secondary', secondary);
                html.style.setProperty('--accent-gradient', gradient);
                html.style.setProperty('--accent-gradient-hover', gradientHover);
                html.style.setProperty('--accent-rgb', `${r}, ${g}, ${b}`);
                html.style.setProperty('--border-color', `rgba(${r}, ${g}, ${b}, 0.2)`);
                html.style.setProperty('--border-glow', `rgba(${r}, ${g}, ${b}, 0.4)`);
                html.style.setProperty('--shadow-glow', `0 0 30px rgba(${r}, ${g}, ${b}, 0.15)`);
                html.style.setProperty('--bg-radial-1', `rgba(${r}, ${g}, ${b}, 0.08)`);

                localStorage.setItem('ml-accent', hex);
                updateSwatchSelection(hex);
            }

            function updateSwatchSelection(hex) {
                document.querySelectorAll('.color-swatch').forEach(s => {
                    s.style.outline = s.dataset.color === hex ? '2px solid var(--text-primary)' : 'none';
                    s.style.outlineOffset = s.dataset.color === hex ? '2px' : '0';
                });
            }

            // Build swatches
            const swatchContainer = document.getElementById('colorSwatches');
            PRESET_COLORS.forEach(c => {
                const btn = document.createElement('button');
                btn.className = 'color-swatch';
                btn.dataset.color = c.hex;
                btn.title = c.name;
                btn.style.cssText = `width:100%; aspect-ratio:1; border-radius:50%; border:2px solid var(--border-color); cursor:pointer; background:${c.hex}; transition:all 0.2s ease;`;
                btn.addEventListener('click', () => applyAccentColor(c.hex));
                btn.addEventListener('mouseenter', () => { btn.style.transform = 'scale(1.15)'; });
                btn.addEventListener('mouseleave', () => { btn.style.transform = 'scale(1)'; });
                swatchContainer.appendChild(btn);
            });

            // Settings panel toggle
            const settingsBtn = document.getElementById('settingsToggle');
            const panel = document.getElementById('colorPickerPanel');
            settingsBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
            });
            document.addEventListener('click', (e) => {
                if (!panel.contains(e.target) && e.target !== settingsBtn) {
                    panel.style.display = 'none';
                }
            });
            panel.addEventListener('click', (e) => e.stopPropagation());

            // Profile Menu Toggle
            const profileBtn = document.getElementById('profileToggle');
            const profileMenu = document.getElementById('profileMenu');
            if (profileBtn && profileMenu) {
                profileBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    profileMenu.style.display = profileMenu.style.display === 'none' ? 'block' : 'none';
                });
                document.addEventListener('click', (e) => {
                    if (!profileMenu.contains(e.target) && e.target !== profileBtn) {
                        profileMenu.style.display = 'none';
                    }
                });
                profileMenu.addEventListener('click', (e) => e.stopPropagation());
            }

            // Custom color input
            const customInput = document.getElementById('customColorInput');
            const applyBtn = document.getElementById('applyCustomColor');
            applyBtn.addEventListener('click', () => {
                let val = customInput.value.trim();
                if (!val) return;
                // HEX format
                if (val.startsWith('#')) {
                    if (/^#[0-9a-fA-F]{3,6}$/.test(val)) {
                        applyAccentColor(val);
                        return;
                    }
                }
                // RGB format (r,g,b)
                const parts = val.split(',').map(s => parseInt(s.trim()));
                if (parts.length === 3 && parts.every(n => !isNaN(n) && n >= 0 && n <= 255)) {
                    const hex = '#' + parts.map(n => n.toString(16).padStart(2, '0')).join('');
                    applyAccentColor(hex);
                    return;
                }
                // If no # prefix, try as hex anyway
                if (/^[0-9a-fA-F]{3,6}$/.test(val)) {
                    applyAccentColor('#' + val);
                    return;
                }
                alert('Formato non valido. Usa #ff5722 oppure 234,88,12');
            });

            // Restore saved accent
            const savedAccent = localStorage.getItem('ml-accent');
            if (savedAccent) {
                applyAccentColor(savedAccent);
            } else {
                updateSwatchSelection('#ea580c');
            }
            // --------------------------------------------------------
            // Custom Select Dropdowns
            // --------------------------------------------------------
            // --------------------------------------------------------
            // Custom Select Dropdowns
            // --------------------------------------------------------
            window.initCustomSelect = function (select) {
                // Se esiste giÃ  un wrapper, lo rimuoviamo per ricrearlo con le nuove opzioni
                if (select.parentNode && select.parentNode.classList.contains('select-wrapper')) {
                    const wrapper = select.parentNode;
                    wrapper.parentNode.insertBefore(select, wrapper);
                    wrapper.remove();
                }

                select.style.display = 'none';

                const wrapper = document.createElement('div');
                wrapper.className = 'select-wrapper ' + (select.className.includes('custom-select') ? 'sort-box-select' : 'form-input-select');

                const trigger = document.createElement('div');
                trigger.className = 'select-trigger';

                const textSpan = document.createElement('span');
                textSpan.textContent = select.options[select.selectedIndex]?.text || '';

                const iconSpan = document.createElement('span');
                iconSpan.className = 'material-symbols-outlined icon-sm';
                iconSpan.textContent = 'expand_more';
                iconSpan.style.transition = 'var(--transition)';
                iconSpan.style.marginLeft = '0.5rem';

                trigger.appendChild(textSpan);
                trigger.appendChild(iconSpan);
                wrapper.appendChild(trigger);

                const optionsContainer = document.createElement('div');
                optionsContainer.className = 'select-options';

                Array.from(select.options).forEach(opt => {
                    const optDiv = document.createElement('div');
                    optDiv.className = 'select-option';
                    if (opt.selected) optDiv.classList.add('selected');
                    optDiv.textContent = opt.text;

                    optDiv.addEventListener('click', () => {
                        select.value = opt.value;
                        textSpan.textContent = opt.text;

                        Array.from(optionsContainer.children).forEach(c => c.classList.remove('selected'));
                        optDiv.classList.add('selected');

                        optionsContainer.style.display = 'none';
                        iconSpan.style.transform = 'rotate(0deg)';
                        trigger.classList.remove('open');

                        select.dispatchEvent(new Event('change', { bubbles: true }));
                    });
                    optionsContainer.appendChild(optDiv);
                });

                wrapper.appendChild(optionsContainer);
                select.parentNode.insertBefore(wrapper, select);
                wrapper.appendChild(select);

                trigger.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const isOpen = optionsContainer.style.display === 'flex';

                    document.querySelectorAll('.select-options').forEach(o => {
                        o.style.display = 'none';
                        o.previousElementSibling.classList.remove('open');
                        o.previousElementSibling.lastElementChild.style.transform = 'rotate(0deg)';
                    });

                    if (!isOpen) {
                        optionsContainer.style.display = 'flex';
                        iconSpan.style.transform = 'rotate(180deg)';
                        trigger.classList.add('open');
                    }
                });
            };

            const selects = document.querySelectorAll('select.custom-select, select.form-input');
            selects.forEach(select => window.initCustomSelect(select));

            document.addEventListener('click', () => {
                document.querySelectorAll('.select-options').forEach(o => {
                    o.style.display = 'none';
                    o.previousElementSibling.classList.remove('open');
                    o.previousElementSibling.lastElementChild.style.transform = 'rotate(0deg)';
                });
            });
        })();
