import React, { useEffect, useState } from 'react';
import { Sun, Moon } from 'lucide-react';

const ThemeToggle = () => {
    const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }, [theme]);

    const toggleTheme = () => {
        setTheme(theme === 'light' ? 'dark' : 'light');
    };

    return (
        <button
            onClick={toggleTheme}
            className="theme-toggle"
            aria-label="Toggle Theme"
        >
            {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}

            <style jsx>{`
                .theme-toggle {
                    background: var(--glass-bg);
                    border: 1px solid var(--glass-border);
                    color: var(--text-primary);
                    width: 40px;
                    height: 40px;
                    border-radius: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    backdrop-filter: blur(10px);
                }

                .theme-toggle:hover {
                    border-color: var(--primary);
                    color: var(--primary);
                    transform: translateY(-2px);
                }
            `}</style>
        </button>
    );
};

export default ThemeToggle;
