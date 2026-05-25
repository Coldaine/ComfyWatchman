import React, { createContext, useContext, useCallback } from 'react';
import { useLocalStorage } from './useLocalStorage';
import { ModelType } from '../types';

export interface UserPreferences {
  // Display preferences
  defaultTab: 'models' | 'workflows' | 'dependencies';
  defaultModelType: ModelType | 'all';
  defaultSortBy: 'name' | 'size' | 'date' | 'usage';
  defaultSortDirection: 'asc' | 'desc';

  // View preferences
  modelsPerPage: number;
  showMissingModelsAlert: boolean;
  compactMode: boolean;

  // Behavior preferences
  autoRefresh: boolean;
  autoRefreshInterval: number; // in seconds
  confirmDelete: boolean;

  // Advanced features
  enableKeyboardShortcuts: boolean;
  enableRealTimeUpdates: boolean;

  // Export/Import
  defaultExportType: 'models' | 'workflows' | 'all';

  // Recommendations
  dismissedRecommendations: string[];
}

const defaultPreferences: UserPreferences = {
  defaultTab: 'models',
  defaultModelType: 'all',
  defaultSortBy: 'name',
  defaultSortDirection: 'asc',
  modelsPerPage: 20,
  showMissingModelsAlert: true,
  compactMode: false,
  autoRefresh: false,
  autoRefreshInterval: 30,
  confirmDelete: true,
  enableKeyboardShortcuts: true,
  enableRealTimeUpdates: false,
  defaultExportType: 'all',
  dismissedRecommendations: [],
};

interface UserPreferencesContextType {
  preferences: UserPreferences;
  updatePreference: <K extends keyof UserPreferences>(key: K, value: UserPreferences[K]) => void;
  resetPreferences: () => void;
  setPreferences: (value: UserPreferences | ((prev: UserPreferences) => UserPreferences)) => void;
}

const UserPreferencesContext = createContext<UserPreferencesContextType | undefined>(undefined);

/**
 * Provider component for user preferences
 */
export function UserPreferencesProvider({ children }: { children: React.ReactNode }) {
  const [preferences, setPreferences, clearPreferences] = useLocalStorage<UserPreferences>(
    'comfyui-dashboard-preferences',
    defaultPreferences
  );

  const updatePreference = useCallback(<K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value
    }));
  }, [setPreferences]);

  const resetPreferences = useCallback(() => {
    clearPreferences();
  }, [clearPreferences]);

  return (
    <UserPreferencesContext.Provider value={{
      preferences,
      updatePreference,
      resetPreferences,
      setPreferences,
    }}>
      {children}
    </UserPreferencesContext.Provider>
  );
}

/**
 * Hook for managing user preferences
 * Automatically persists to localStorage and syncs via Context
 */
export function useUserPreferences() {
  const context = useContext(UserPreferencesContext);
  if (context === undefined) {
    throw new Error('useUserPreferences must be used within a UserPreferencesProvider');
  }
  return context;
}

