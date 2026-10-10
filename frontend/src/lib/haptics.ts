/** Short vibration on phones that support it (Android Chrome); silently no-op elsewhere. */
export function buzz(pattern: number | number[] = 12) {
  if (typeof navigator !== 'undefined' && 'vibrate' in navigator) navigator.vibrate(pattern)
}
