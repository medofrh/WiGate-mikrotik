<script setup>
import { ref } from 'vue'
import { fetchVouchers } from '../api'
import { copyText, downloadBlob, downloadCsv, downloadText } from '../utils'

const props = defineProps({
  result: { type: Object, required: true }
})
const emit = defineEmits(['reset', 'error'])

const pdfBusy = ref(false)
const copied = ref(false)

function onCsv() {
  downloadCsv(props.result.csv, 'benutzer.csv')
}

function onCommands() {
  downloadText(props.result.commands, 'mikrotik-befehle.txt')
}

async function onCopy() {
  const ok = await copyText(props.result.commands)
  if (!ok) {
    emit('error', 'Das Kopieren hat nicht geklappt. Bitte die Befehle herunterladen.')
    return
  }
  copied.value = true
  setTimeout(() => (copied.value = false), 2000)
}

async function onPdf() {
  pdfBusy.value = true
  try {
    const blob = await fetchVouchers(props.result.users)
    downloadBlob(blob, 'gutscheine.pdf')
  } catch (error) {
    emit('error', error.message)
  } finally {
    pdfBusy.value = false
  }
}

const button =
  'inline-flex items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold shadow-sm transition disabled:opacity-60'
</script>

<template>
  <div class="space-y-5">
    <div class="grid gap-3 sm:grid-cols-2">
      <button type="button" :class="[button, 'bg-blue-600 text-white hover:bg-blue-700']" @click="onPdf" :disabled="pdfBusy">
        {{ pdfBusy ? 'PDF wird erstellt …' : 'Gutschein-PDF herunterladen' }}
      </button>
      <button type="button" :class="[button, 'bg-slate-900 text-white hover:bg-slate-800']" @click="onCsv">
        Benutzer-CSV herunterladen
      </button>
      <button type="button" :class="[button, 'bg-white text-slate-800 ring-1 ring-slate-300 hover:bg-slate-50']" @click="onCommands">
        MikroTik-Befehle herunterladen
      </button>
      <button
        type="button"
        :class="[button, copied ? 'bg-emerald-600 text-white' : 'bg-white text-slate-800 ring-1 ring-slate-300 hover:bg-slate-50']"
        @click="onCopy"
      >
        {{ copied ? 'Befehle kopiert!' : 'MikroTik-Befehle kopieren' }}
      </button>
    </div>

    <p class="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
      Die Passwörter werden nirgends gespeichert. Bitte die Dateien jetzt herunterladen –
      nach dem Neuladen der Seite sind sie nicht mehr abrufbar.
    </p>

    <div class="overflow-hidden rounded-xl ring-1 ring-slate-200">
      <div class="max-h-96 overflow-y-auto">
        <table class="w-full text-left text-sm">
          <thead class="sticky top-0 bg-slate-50 text-xs tracking-wide text-slate-500 uppercase">
            <tr>
              <th class="px-4 py-2 font-medium">Name</th>
              <th class="px-4 py-2 font-medium">Geburtstag</th>
              <th class="px-4 py-2 font-medium">Benutzer</th>
              <th class="px-4 py-2 font-medium">Passwort</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="user in result.users" :key="user.username">
              <td class="px-4 py-2">
                <span v-if="user.blank" class="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                  Blank
                </span>
                <span v-else>{{ user.firstname }} {{ user.lastname }}</span>
              </td>
              <td class="px-4 py-2 text-slate-500">{{ user.blank ? '—' : user.birthday || '—' }}</td>
              <td class="mono px-4 py-2 font-medium">{{ user.username }}</td>
              <td class="mono px-4 py-2 font-medium">{{ user.password }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <button type="button" class="text-sm font-medium text-blue-700 hover:underline" @click="emit('reset')">
      Neue Liste erstellen
    </button>
  </div>
</template>
