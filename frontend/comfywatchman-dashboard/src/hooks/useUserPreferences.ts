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
};

/**
 * Hook for managing user preferences
 * Automatically persists to localStorage
 */
export function useUserPreferences() {
  const [preferences, setPreferences, clearPreferences] = useLocalStorage<UserPreferences>(
    'comfyui-dashboard-preferences',
    defaultPreferences
  );

  const updatePreference = <K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const resetPreferences = () => {
    clearPreferences();
  };

  return {
    preferences,
    updatePreference,
    resetPreferences,
    setPreferences,
  };
}
