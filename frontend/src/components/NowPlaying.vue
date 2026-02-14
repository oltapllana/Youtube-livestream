<template>
  <div class="now-playing">
    <div class="np-info">
      <span v-if="program" class="np-live-badge">LIVE</span>
      <span class="np-title">{{ title }}</span>
      <span class="np-channel">{{ channel }}</span>
    </div>
    <div class="np-time">{{ timeRange }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { minsToTime, cleanTitle } from '../api.js'

const props = defineProps({
  program: { type: Object, default: null },
  nextProgram: { type: Object, default: null },
})

const title = computed(() => {
  if (props.program) return cleanTitle(props.program.program_id)
  if (props.nextProgram) return 'Waiting…'
  return '—'
})

const channel = computed(() => {
  if (props.program) return `Channel ${props.program.channel_id}`
  if (props.nextProgram) {
    return `Next: ${cleanTitle(props.nextProgram.program_id)} at ${minsToTime(props.nextProgram.start)}`
  }
  return ''
})

const timeRange = computed(() => {
  if (props.program) {
    return `${minsToTime(props.program.start)} — ${minsToTime(props.program.end)}`
  }
  return ''
})
</script>
