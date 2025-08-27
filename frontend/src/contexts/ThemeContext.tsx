import React, { createContext, useContext, useState, useEffect } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>(() => {
    // Get saved theme from localStorage or default to light
    const savedTheme = localStorage.getItem('chatbot-theme') as Theme;
    return savedTheme || 'light';
  });

  useEffect(() => {
    // Apply theme to document
    document.documentElement.setAttribute('data-bs-theme', theme);
    document.body.className = theme === 'dark' ? 'bg-dark text-light' : 'bg-light text-dark';
    
    // Save theme to localStorage
    localStorage.setItem('chatbot-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};