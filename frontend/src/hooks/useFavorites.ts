import { useState, useEffect } from 'react';

interface FavoriteMessage {
  id: number;
  content: string;
  timestamp: string;
  sessionId: number;
  sessionName: string;
}

export const useFavorites = () => {
  const [favorites, setFavorites] = useState<FavoriteMessage[]>([]);

  useEffect(() => {
    // Load favorites from localStorage
    const savedFavorites = localStorage.getItem('chatbot-favorites');
    if (savedFavorites) {
      try {
        setFavorites(JSON.parse(savedFavorites));
      } catch (error) {
        console.error('Error loading favorites:', error);
      }
    }
  }, []);

  const saveFavorites = (newFavorites: FavoriteMessage[]) => {
    setFavorites(newFavorites);
    localStorage.setItem('chatbot-favorites', JSON.stringify(newFavorites));
  };

  const addFavorite = (message: FavoriteMessage) => {
    if (favorites.some(fav => fav.id === message.id)) return false; // Already favorited
    
    const newFavorites = [...favorites, message];
    saveFavorites(newFavorites);
    return true;
  };

  const removeFavorite = (messageId: number) => {
    const newFavorites = favorites.filter(fav => fav.id !== messageId);
    saveFavorites(newFavorites);
    return true;
  };

  const isFavorite = (messageId: number): boolean => {
    return favorites.some(fav => fav.id === messageId);
  };

  const toggleFavorite = (message: FavoriteMessage): boolean => {
    if (isFavorite(message.id)) {
      removeFavorite(message.id);
      return false;
    } else {
      addFavorite(message);
      return true;
    }
  };

  const clearAllFavorites = () => {
    setFavorites([]);
    localStorage.removeItem('chatbot-favorites');
  };

  return {
    favorites,
    addFavorite,
    removeFavorite,
    isFavorite,
    toggleFavorite,
    clearAllFavorites
  };
};