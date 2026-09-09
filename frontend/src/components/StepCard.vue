<script setup>
defineProps({
  step: { type: [String, Number], required: true },
  title: { type: String, required: true },
  hint: { type: String, default: '' },
  done: { type: Boolean, default: false }
})
</script>

<template>
  <section class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 sm:p-6">
    <header class="mb-4 flex items-start gap-3">
      <span
        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold"
        :class="done ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-600 text-white'"
      >
        <svg v-if="done" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path
            fill-rule="evenodd"
            d="M16.7 5.3a1 1 0 0 1 0 1.4l-7.5 7.5a1 1 0 0 1-1.4 0l-3.5-3.5a1 1 0 1 1 1.4-1.4l2.8 2.79 6.8-6.79a1 1 0 0 1 1.4 0Z"
            clip-rule="evenodd"
          />
        </svg>
        <template v-else>{{ step }}</template>
      </span>
      <div class="min-w-0">
        <h2 class="text-base font-semibold leading-8 text-slate-900">{{ title }}</h2>
        <p v-if="hint" class="mt-0.5 text-sm text-slate-500">{{ hint }}</p>
      </div>
    </header>
    <slot />
  </section>
</template>
