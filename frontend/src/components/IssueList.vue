<script setup>
defineProps({
  title: { type: String, required: true },
  items: { type: Array, default: () => [] },
  tone: { type: String, default: 'error' }
})

const styles = {
  error: 'border-red-200 bg-red-50 text-red-800',
  warning: 'border-amber-200 bg-amber-50 text-amber-800'
}
</script>

<template>
  <div v-if="items.length" class="rounded-xl border p-4 text-sm" :class="styles[tone]">
    <p class="font-semibold">{{ title }}</p>
    <ul class="mt-2 space-y-1">
      <li v-for="(issue, index) in items" :key="index" class="flex gap-2">
        <span class="opacity-60">•</span>
        <span>
          <span v-if="issue.line" class="font-medium">Zeile {{ issue.line }}:</span>
          {{ issue.message }}
        </span>
      </li>
    </ul>
  </div>
</template>
