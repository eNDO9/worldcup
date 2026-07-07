/** In-memory TTL memo for a zero-arg async function. Fine for our single
 * long-running Node server on Coolify (mirrors st.cache_data ttl=N). */
export function ttlCached<T>(seconds: number, fn: () => Promise<T>): () => Promise<T> {
  let value: T | undefined;
  let fetchedAt = 0;
  return async () => {
    if (value === undefined || Date.now() - fetchedAt > seconds * 1000) {
      value = await fn();
      fetchedAt = Date.now();
    }
    return value;
  };
}
