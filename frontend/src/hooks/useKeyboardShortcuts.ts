import { useEffect } from 'react';

interface KeyboardShortcuts {
  onNewSession?: () => void;
  onSearch?: () => void;
  onToggleTheme?: () => void;
  onToggleTemplates?: () => void;
  onToggleFavorites?: () => void;
  onExport?: () => void;
  onSend?: () => void;
  isInputFocused?: boolean;
}

export const useKeyboardShortcuts = ({
  onNewSession,
  onSearch,
  onToggleTheme,
  onToggleTemplates,
  onToggleFavorites,
  onExport,
  onSend,
  isInputFocused = false
}: KeyboardShortcuts) => {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const { key, ctrlKey, altKey, metaKey, shiftKey } = event;
      const isModifierPressed = ctrlKey || metaKey; // Support both Ctrl (Windows/Linux) and Cmd (Mac)
      
      // Don't interfere when typing in inputs (except for specific shortcuts)
      const activeElement = document.activeElement;
      const isTyping = activeElement?.tagName === 'INPUT' || 
                      activeElement?.tagName === 'TEXTAREA' || 
                      activeElement?.getAttribute('contenteditable') === 'true';
      
      // Global shortcuts that work even when typing
      if (isModifierPressed) {
        switch (key.toLowerCase()) {
          case 'n':
            if (onNewSession) {
              event.preventDefault();
              onNewSession();
            }
            break;
            
          case 'f':
            if (onSearch && !isTyping) { // Don't interfere with browser's find
              event.preventDefault();
              onSearch();
            }
            break;
            
          case 'd':
            if (onToggleTheme && altKey) {
              event.preventDefault();
              onToggleTheme();
            }
            break;
            
          case 't':
            if (onToggleTemplates && shiftKey) {
              event.preventDefault();
              onToggleTemplates();
            }
            break;
            
          case 's':
            if (onToggleFavorites && shiftKey && !isTyping) {
              event.preventDefault();
              onToggleFavorites();
            }
            break;
            
          case 'e':
            if (onExport && shiftKey && !isTyping) {
              event.preventDefault();
              onExport();
            }
            break;
        }
      }
      
      // Enter key for sending messages (only when input is focused)
      if (key === 'Enter' && !shiftKey && isInputFocused && onSend) {
        event.preventDefault();
        onSend();
      }
      
      // Escape key shortcuts
      if (key === 'Escape') {
        // Close any open modals/panels by dispatching a custom event
        window.dispatchEvent(new CustomEvent('closeModals'));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    onNewSession,
    onSearch,
    onToggleTheme,
    onToggleTemplates,
    onToggleFavorites,
    onExport,
    onSend,
    isInputFocused
  ]);

  // Return the shortcuts for display in help/tooltip
  return {
    shortcuts: [
      { key: 'Ctrl+N', description: 'Nueva conversación' },
      { key: 'Ctrl+F', description: 'Buscar en conversaciones' },
      { key: 'Ctrl+Alt+D', description: 'Cambiar tema claro/oscuro' },
      { key: 'Ctrl+Shift+T', description: 'Mostrar templates' },
      { key: 'Ctrl+Shift+S', description: 'Mostrar favoritos' },
      { key: 'Ctrl+Shift+E', description: 'Exportar conversación' },
      { key: 'Enter', description: 'Enviar mensaje (en campo de texto)' },
      { key: 'Esc', description: 'Cerrar modales' }
    ]
  };
};