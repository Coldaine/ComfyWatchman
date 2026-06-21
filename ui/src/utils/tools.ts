export const mergeByKeyCombine = <T extends Record<string, any>>(a: T[], b: T[], key: keyof T): T[] => {
  const map = new Map<any, T>();
  for (const item of a) map.set(item[key], { ...item });
  for (const item of b) {
    const _key = item[key];
    map.set(_key, { ...(map.get(_key) ?? {}), ...item });
  }
  return Array.from(map.values());
}

export const isObj = (value: unknown): value is Record<string, unknown> => 
  value !== null && typeof value === 'object' && !Array.isArray(value);