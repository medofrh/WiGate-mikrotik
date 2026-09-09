<script setup>
import { computed } from 'vue'

const props = defineProps({
  people: { type: Array, default: () => [] },
  imported: { type: Number, default: 0 },
  extra: { type: Number, default: 0 },
  total: { type: Number, default: 0 },
  server: { type: String, default: '' },
  profile: { type: String, default: '' },
  blockReason: { type: String, default: '' },
  busy: { type: Boolean, default: false }
})
defineEmits(['generate'])

const PREVIEW_ROWS = 10
const visible = computed(() => props.people.slice(0, PREVIEW_ROWS))
const hidden = computed(() => Math.max(0, props.people.length - PREVIEW_ROWS))
</script>

<template>
  <div class="space-y-5">
    <div class="grid grid-cols-3 gap-3">
      <div class="rounded-xl bg-slate-50 p-4 text-center ring-1 ring-slate-200">
        <p class="text-2xl font-semibold text-slate-900">{{ imported }}</p>
        <p class="mt-1 text-xs font-medium tracking-wide text-slate-500 uppercase">Importiert</p>
      </div>
      <div class="rounded-xl bg-slate-50 p-4 text-center ring-1 ring-slate-200">
        <p class="text-2xl font-semibold text-slate-900">{{ extra }}</p>
        <p class="mt-1 text-xs font-medium tracking-wide text-slate-500 uppercase">Zusatz</p>
      </div>
      <div class="rounded-xl bg-blue-50 p-4 text-center ring-1 ring-blue-200">
        <p class="text-2xl font-semibold text-blue-700">{{ total }}</p>
        <p class="mt-1 text-xs font-medium tracking-wide text-blue-600 uppercase">Gesamt</p>
      </div>
    </div>

    <div v-if="visible.length" class="overflow-hidden rounded-xl ring-1 ring-slate-200">
      <table class="w-full text-left text-sm">
        <thead class="bg-slate-50 text-xs tracking-wide text-slate-500 uppercase">
          <tr>
            <th class="px-4 py-2 font-medium">Vorname</th>
            <th class="px-4 py-2 font-medium">Nachname</th>
            <th class="px-4 py-2 font-medium">Geburtstag</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="(person, index) in visible" :key="index">
            <td class="px-4 py-2">{{ person.firstname }}</td>
            <td class="px-4 py-2">{{ person.lastname }}</td>
            <td class="px-4 py-2 text-slate-500">{{ person.birthday || '—' }}</td>
          </tr>
        </tbody>
      </table>
      <p v-if="hidden" class="bg-slate-50 px-4 py-2 text-xs text-slate-500">
        … und {{ hidden }} weitere
      </p>
    </div>

    <p class="text-sm text-slate-600">
      Server <span class="mono font-medium text-slate-900">{{ server || '—' }}</span>
      · Profil <span class="mono font-medium text-slate-900">{{ profile || '—' }}</span>
    </p>

    <div>
      <button
        type="button"
        class="w-full rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300 sm:w-auto"
        :disabled="!!blockReason || busy"
        @click="$emit('generate')"
      >
        {{ busy ? 'Benutzer werden erzeugt …' : `${total} Benutzer erzeugen` }}
      </button>
      <p v-if="blockReason" class="mt-2 text-sm text-slate-500">{{ blockReason }}</p>
    </div>
  </div>
</template>
