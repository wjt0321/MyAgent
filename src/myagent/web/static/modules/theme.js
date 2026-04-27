export default (Base) => class ThemeMixin extends Base {
    getEffectiveTheme() {
        if (this.currentTheme === 'auto') {
            return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }
        return this.currentTheme;
    }

    initTheme() {
        const effective = this.getEffectiveTheme();
        document.body.className = `theme-${effective}`;
        this.updateHLJSTheme();
        this.updateThemeIcon();
    }

    toggleTheme() {
        const themes = ['dark', 'light', 'auto'];
        const idx = themes.indexOf(this.currentTheme);
        this.currentTheme = themes[(idx + 1) % themes.length];
        this.applyTheme();
    }

    applyTheme() {
        const effective = this.getEffectiveTheme();
        document.body.className = `theme-${effective}`;
        localStorage.setItem('myagent-theme', this.currentTheme);
        this.updateHLJSTheme();
        this.updateThemeIcon();

        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === this.currentTheme);
        });
    }

    updateHLJSTheme() {
        const effective = this.getEffectiveTheme();
        const link = document.getElementById('hljs-theme');
        if (link) {
            const theme = effective === 'dark' ? 'atom-one-dark' : 'github';
            link.href = `https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/${theme}.min.css`;
        }
    }

    updateThemeIcon() {
        const icon = document.getElementById('theme-icon');
        if (!icon) return;
        const effective = this.getEffectiveTheme();
        if (effective === 'dark') {
            icon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';
        } else {
            icon.innerHTML = '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>';
        }
    }

    setupSystemThemeListener() {
        const media = window.matchMedia('(prefers-color-scheme: dark)');
        media.addEventListener('change', () => {
            if (this.currentTheme === 'auto') {
                this.applyTheme();
            }
        });
    }
};
