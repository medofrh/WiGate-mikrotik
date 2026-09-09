<script setup>
import { ref } from 'vue'

defineProps({
  filename: { type: String, default: '' },
  count: { type: Number, default: 0 },
  busy: { type: Boolean, default: false },
  ok: { type: Boolean, default: false }
})
const emit = defineEmits(['file'])

const dragging = ref(false)
const input = ref(null)

function choose(files) {
  const file = files && files[0]
  if (file) emit('file', file)
}

function onDrop(event) {
  dragging.value = false
  choose(event.dataTransfer.files)
}

function onSelect(event) {
  choose(event.target.files)
  event.target.value = ''
}
</script>

<template>
  <div>
    <div
      class="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-8 text-center transition"
      :class="dragging ? 'border-blue-500 bg-blue-50' : 'border-slate-300 bg-slate-50 hover:border-blue-400 hover:bg-blue-50/50'"
      role="button"
      tabindex="0"
      @click="input.click()"
      @keydown.enter.prevent="input.click()"
      @keydown.space.prevent="input.click()"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="onDrop"
    >
      <svg class="h-8 w-8 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 16V4m0 0L8 8m4-4 4 4M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
      </svg>
      <p class="mt-3 text-sm font-medium text-slate-700">
        CSV-Datei hierher ziehen oder klicken zum Auswählen
      </p>
      <p class="mt-1 text-xs text-slate-500">Spalten: firstname, lastname, birthday</p>
      <input ref="input" type="file" accept=".csv,.txt,text/csv" class="hidden" @change="onSelect" />
    </div>

    <p v-if="busy" class="mt-3 text-sm text-slate-500">Datei wird gelesen …</p>
    <div
      v-else-if="filename"
      class="mt-3 flex flex-wrap items-center gap-2 rounded-xl px-4 py-3 text-sm"
      :class="ok ? 'bg-emerald-50 text-emerald-800' : 'bg-slate-100 text-slate-700'"
    >
      <span class="font-medium">{{ filename }}</span>
      <span class="opacity-60">·</span>
      <span>{{ count }} {{ count === 1 ? 'Person' : 'Personen' }} gelesen</span>
    </div>
  </div>
</template>
