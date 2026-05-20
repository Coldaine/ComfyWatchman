import { useEffect } from 'react';

export type KeyboardShortcut = {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  meta?: boolean;
};

/**
 * Hook for registering keyboard shortcuts
 * Example: useKeyboardShortcut({ key: 's', ctrl: true }, handleSave)
 */
export function useKeyboardShortcut(
  shortcut: KeyboardShortcut,
  callback: () => void,
  enabled: boolean = true
): void {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      const { key, ctrl, shift, alt, meta } = shortcut;

      // Check if all modifiers match
      const ctrlMatch = ctrl === undefined || event.ctrlKey === ctrl;
      const shiftMatch = shift === undefined || event.shiftKey === shift;
      const altMatch = alt === undefined || event.altKey === alt;
      const metaMatch = meta === undefined || event.metaKey === meta;

      // Check if key matches (case insensitive)
      const keyMatch = event.key.toLowerCase() === key.toLowerCase();

      if (keyMatch && ctrlMatch && shiftMatch && altMatch && metaMatch) {
        event.preventDefault();
        callback();
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [shortcut, callback, enabled]);
}

/**
 * Hook for registering multiple keyboard shortcuts
 */
export function useKeyboardShortcuts(
  shortcuts: Array<{ shortcut: KeyboardShortcut; callback: () => void }>,
  enabled: boolean = true
): void {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      for (const { shortcut, callback } of shortcuts) {
        const { key, ctrl, shift, alt, meta } = shortcut;

        const ctrlMatch = ctrl === undefined || event.ctrlKey === ctrl;
        const shiftMatch = shift === undefined || event.shiftKey === shift;
        const altMatch = alt === undefined || event.altKey === alt;
        const metaMatch = meta === undefined || event.metaKey === meta;
        const keyMatch = event.key.toLowerCase() === key.toLowerCase();

        if (keyMatch && ctrlMatch && shiftMatch && altMatch && metaMatch) {
          event.preventDefault();
          callback();
          break; // Only execute first matching shortcut
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [shortcuts, enabled]);
}
