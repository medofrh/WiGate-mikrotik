<script setup>
import { computed } from 'vue'
import { DEFAULT_QR_TEMPLATE } from '../storage'

const server = defineModel('server', { type: String, default: '' })
const profile = defineModel('profile', { type: String, default: '' })
const extraUsers = defineModel('extraUsers', { type: Number, default: 0 })
const qrTemplate = defineModel('qrTemplate', { type: String, default: '' })

const NAME_PATTERN = /^[A-Za-z0-9._-]{1,64}$/
const MAX_EXTRA = 500

const serverError = computed(() =>
  server.value && !NAME_PATTERN.test(server.value.trim())
    ? 'Erlaubt sind Buchstaben, Zahlen, Punkt, Bindestrich und Unterstrich.'
    : ''
)
const profileError = computed(() =>
  profile.value && !NAME_PATTERN.test(profile.value.trim())
    ? 'Erlaubt sind Buchstaben, Zahlen, Punkt, Bindestrich und Unterstrich.'
    : ''
)
const qrError = computed(() => {
  const template = (qrTemplate.value || '').replace(/\{\{|\}\}/g, (match) => match[0])
  if (!template.includes('{username}') || !template.includes('{password}')) {
    return 'Der Link muss {username} und {password} enthalten.'
  }
  return ''
})
const qrExample = computed(() =>
  (qrTemplate.value || '')
    .replace(/\{\{?username\}?\}/g, 'acb-k7x')
    .replace(/\{\{?password\}?\}/g, 'k7mrp4qz')
)

function step(amount) {
  const next = (Number(extraUsers.value) || 0) + amount
  extraUsers.value = Math.min(MAX_EXTRA, Math.max(0, next))
}

function onExtraInput(event) {
  const value = Number(event.target.value)
  extraUsers.value = Number.isFinite(value) ? Math.min(MAX_EXTRA, Math.max(0, Math.trunc(value))) : 0
}

const fieldClass =
  'w-full rounded-lg border px-3 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200'
</script>

<template>
  <div class="space-y-5">
    <div class="grid gap-4 sm:grid-cols-2">
      <div>
        <label for="server" class="mb-1 block text-sm font-medium text-slate-700">Server</label>
        <input
          id="server"
          v-model="server"
          type="text"
          placeholder="hotspot1"
          autocomplete="off"
          spellcheck="false"
          :class="[fieldClass, serverError ? 'border-red-400' : 'border-slate-300']"
        />
        <p v-if="serverError" class="mt-1 text-xs text-red-600">{{ serverError }}</p>
      </div>

      <div>
        <label for="profile" class="mb-1 block text-sm font-medium text-slate-700">Profil</label>
        <input
          id="profile"
          v-model="profile"
          type="text"
          placeholder="teachers"
          autocomplete="off"
          spellcheck="false"
          :class="[fieldClass, profileError ? 'border-red-400' : 'border-slate-300']"
        />
        <p v-if="profileError" class="mt-1 text-xs text-red-600">{{ profileError }}</p>
      </div>
    </div>

    <div>
      <label for="extra" class="mb-1 block text-sm font-medium text-slate-700">
        Zusatz-Benutzer (Blank)
      </label>
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="h-10 w-10 rounded-lg border border-slate-300 text-lg font-semibold text-slate-600 transition hover:bg-slate-100 disabled:opacity-40"
          :disabled="extraUsers <= 0"
          aria-label="Weniger Zusatz-Benutzer"
          @click="step(-1)"
        >
          −
        </button>
        <input
          id="extra"
          :value="extraUsers"
          type="number"
          min="0"
          :max="MAX_EXTRA"
          inputmode="numeric"
          class="w-24 rounded-lg border border-slate-300 px-3 py-2 text-center text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
          @input="onExtraInput"
        />
        <button
          type="button"
          class="h-10 w-10 rounded-lg border border-slate-300 text-lg font-semibold text-slate-600 transition hover:bg-slate-100 disabled:opacity-40"
          :disabled="extraUsers >= MAX_EXTRA"
          aria-label="Mehr Zusatz-Benutzer"
          @click="step(1)"
        >
          +
        </button>
        <p class="text-xs text-slate-500">
          Zusätzliche Zugänge ohne Namen, für kurzfristige Teilnehmer.
        </p>
      </div>
    </div>

    <div>
      <label for="qr" class="mb-1 block text-sm font-medium text-slate-700">QR-Login-Link</label>
      <input
        id="qr"
        v-model="qrTemplate"
        type="text"
        spellcheck="false"
        autocomplete="off"
        :placeholder="DEFAULT_QR_TEMPLATE"
        :class="[fieldClass, 'mono', qrError ? 'border-red-400' : 'border-slate-300']"
      />
      <p v-if="qrError" class="mt-1 text-xs text-red-600">{{ qrError }}</p>
      <p v-else class="mt-1 truncate text-xs text-slate-500">
        Beispiel: <span class="mono">{{ qrExample }}</span>
      </p>
    </div>
  </div>
</template>
