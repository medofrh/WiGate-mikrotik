// Merkt sich die zuletzt benutzten Einstellungen im Browser.
const KEY = 'wigate.settings'

export const DEFAULT_QR_TEMPLATE =
  'http://hotspot.acb/login?username={username}&password={password}'

export function defaultSettings() {
  return { server: '', profile: '', extraUsers: 0, qrTemplate: DEFAULT_QR_TEMPLATE }
}

export function loadSettings() {
  try {
    const stored = JSON.parse(localStorage.getItem(KEY) || '{}')
    return { ...defaultSettings(), ...stored }
  } catch {
    return defaultSettings()
  }
}

export function saveSettings(settings) {
  try {
    localStorage.setItem(KEY, JSON.stringify({ ...settings }))
  } catch {
    /* Privater Modus o. Ä.: Einstellungen werden dann nicht gemerkt. */
  }
}
