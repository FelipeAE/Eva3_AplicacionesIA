import { useState, useCallback } from 'react';

export interface SessionWithTags {
  id: number;
  name: string;
  tags: string[];
  created_at: string;
  finished_at?: string;
}

export const useConversationTags = () => {
  const [, forceUpdate] = useState({});

  const getSessionTags = useCallback((sessionId: number): string[] => {
    const stored = localStorage.getItem(`session-tags-${sessionId}`);
    return stored ? JSON.parse(stored) : [];
  }, []);

  const setSessionTags = useCallback((sessionId: number, tags: string[]) => {
    localStorage.setItem(`session-tags-${sessionId}`, JSON.stringify(tags));
    forceUpdate({});
  }, []);

  const getAllSessionsWithTags = useCallback((): SessionWithTags[] => {
    const sessions: SessionWithTags[] = [];
    
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith('session-tags-')) {
        try {
          const sessionId = parseInt(key.replace('session-tags-', ''));
          const tags = JSON.parse(localStorage.getItem(key) || '[]');
          
          // Try to get session info from another localStorage key if available
          // This is a simplified version - in a real app you'd fetch from API
          sessions.push({
            id: sessionId,
            name: `Conversación ${sessionId}`,
            tags,
            created_at: new Date().toISOString(),
          });
        } catch (e) {
          // Skip invalid entries
        }
      }
    }
    
    return sessions.sort((a, b) => b.id - a.id);
  }, []);

  const getPopularTags = useCallback((limit: number = 10): Array<{ tag: string; count: number }> => {
    const tagCounts: { [key: string]: number } = {};
    
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith('session-tags-')) {
        try {
          const tags = JSON.parse(localStorage.getItem(key) || '[]');
          tags.forEach((tag: string) => {
            tagCounts[tag] = (tagCounts[tag] || 0) + 1;
          });
        } catch (e) {
          // Skip invalid entries
        }
      }
    }
    
    return Object.entries(tagCounts)
      .map(([tag, count]) => ({ tag, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, limit);
  }, []);

  const searchSessionsByTags = useCallback((tags: string[]): SessionWithTags[] => {
    if (tags.length === 0) return getAllSessionsWithTags();
    
    return getAllSessionsWithTags().filter(session =>
      tags.some(tag => session.tags.includes(tag))
    );
  }, [getAllSessionsWithTags]);

  const getTagSuggestions = useCallback((partial: string): string[] => {
    const allTags = new Set<string>();
    
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith('session-tags-')) {
        try {
          const tags = JSON.parse(localStorage.getItem(key) || '[]');
          tags.forEach((tag: string) => allTags.add(tag));
        } catch (e) {
          // Skip invalid entries
        }
      }
    }
    
    return Array.from(allTags)
      .filter(tag => tag.toLowerCase().includes(partial.toLowerCase()))
      .sort();
  }, []);

  return {
    getSessionTags,
    setSessionTags,
    getAllSessionsWithTags,
    getPopularTags,
    searchSessionsByTags,
    getTagSuggestions,
  };
};