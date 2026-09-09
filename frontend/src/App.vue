<script setup>
import { computed, reactive, ref, watch } from 'vue'
import FileDrop from './components/FileDrop.vue'
import IssueList from './components/IssueList.vue'
import PreviewCard from './components/PreviewCard.vue'
import ResultCard from './components/ResultCard.vue'
import SettingsForm from './components/SettingsForm.vue'
import StepCard from './components/StepCard.vue'
import { generateUsers, parseCsv } from './api'
import { loadSettings, saveSettings } from './storage'

const MAX_EXTRA = 500
const MAX_TOTAL = 2000
const NAME_PATTERN = /^[A-Za-z0-9._-]{1,64}$/

const settings = reactive(loadSettings())
watch(settings, () => saveSettings(settings), { deep: true })

const upload = reactive({ filename: '', people: [], errors: [], warnings: [] })
const uploading = ref(false)
const generating = ref(false)
const message = ref('')
const result = ref(null)

const imported = computed(() => upload.people.length)
const extra = computed(() => Number(settings.extraUsers) || 0)
const total = computed(() => imported.value + extra.value)
const csvOk = computed(() => upload.filename !== '' && upload.errors.length === 0)

const blockReason = computed(() => {
  if (upload.errors.length) return 'Bitte zuerst die Fehler in der CSV-Datei beheben.'
  if (total.value < 1) return 'Bitte eine CSV-Datei hochladen oder Zusatz-Benutzer eintragen.'
  if (!settings.server.trim() || !settings.profile.trim()) {
    return 'Bitte Server und Profil eintragen.'
  }
  if (!NAME_PATTERN.test(settings.server.trim()) || !NAME_PATTERN.test(settings.profile.trim())) {
    return 'Server und Profil enthalten unerlaubte Zeichen.'
  }
  if (extra.value > MAX_EXTRA) return `Es sind höchstens ${MAX_EXTRA} Zusatz-Benutzer möglich.`
  if (total.value > MAX_TOTAL) return `Es können höchstens ${MAX_TOTAL} Benutzer erzeugt werden.`
  return ''
})

async function onFile(file) {
  uploading.value = true
  message.value = ''
  result.value = null
  try {
    const data = await parseCsv(file)
    upload.filename = data.filename || file.name
    upload.people = data.people
    upload.errors = data.errors
    upload.warnings = data.warnings
  } catch (error) {
    resetUpload()
    message.value = error.message
  } finally {
    uploading.value = false
  }
}

async function onGenerate() {
  generating.value = true
  message.value = ''
  try {
    result.value = await generateUsers({
      people: upload.people,
      extra_users: extra.value,
      server: settings.server.trim(),
      profile: settings.profile.trim(),
      qr_template: settings.qrTemplate
    })
  } catch (error) {
    message.value = error.message
  } finally {
    generating.value = false
  }
}

function resetUpload() {
  upload.filename = ''
  upload.people = []
  upload.errors = []
  upload.warnings = []
}

function resetAll() {
  resetUpload()
  result.value = null
  message.value = ''
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<template>
  <div class="mx-auto max-w-3xl px-4 py-8 sm:py-12">
    <header class="mb-8">
      <h1 class="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">WiGate</h1>
      <p class="mt-1 text-slate-600">MikroTik Hotspot-Benutzer und Gutscheine erstellen.</p>
    </header>

    <div
      v-if="message"
      class="mb-6 flex items-start justify-between gap-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
    >
      <span>{{ message }}</span>
      <button type="button" class="font-medium hover:underline" @click="message = ''">Schließen</button>
    </div>

    <div class="space-y-6">
      <StepCard step="1" title="CSV-Datei hochladen" hint="Spalten: firstname, lastname, birthday" :done="csvOk">
        <div class="space-y-4">
          <FileDrop
            :filename="upload.filename"
            :count="imported"
            :busy="uploading"
            :ok="csvOk"
            @file="onFile"
          />
          <IssueList title="Diese Zeilen konnten nicht gelesen werden:" :items="upload.errors" tone="error" />
          <IssueList title="Hinweise:" :items="upload.warnings" tone="warning" />
          <p class="text-xs text-slate-500">
            Ohne CSV-Datei können auch nur Zusatz-Benutzer erzeugt werden.
          </p>
        </div>
      </StepCard>

      <StepCard
        step="2"
        title="MikroTik-Einstellungen"
        hint="Wird beim nächsten Mal automatisch wieder eingetragen."
        :done="!!settings.server.trim() && !!settings.profile.trim()"
      >
        <SettingsForm
          v-model:server="settings.server"
          v-model:profile="settings.profile"
          v-model:extra-users="settings.extraUsers"
          v-model:qr-template="settings.qrTemplate"
        />
      </StepCard>

      <StepCard step="3" title="Vorschau" hint="Bitte vor dem Erzeugen kurz prüfen." :done="!!result">
        <PreviewCard
          :people="upload.people"
          :imported="imported"
          :extra="extra"
          :total="total"
          :server="settings.server"
          :profile="settings.profile"
          :block-reason="blockReason"
          :busy="generating"
          @generate="onGenerate"
        />
      </StepCard>

      <StepCard
        v-if="result"
        step="4"
        title="Fertig"
        :hint="`${result.counts.total} Benutzer erzeugt.`"
        :done="true"
      >
        <ResultCard :result="result" @reset="resetAll" @error="message = $event" />
      </StepCard>
    </div>

    <footer class="mt-10 text-center text-xs text-slate-400">
      WiGate · läuft vollständig lokal, es werden keine Daten an Dritte gesendet.
    </footer>
  </div>
</template>
