<template>
  <div class="sched-card" :class="status">
    <div class="sched-thumb">
      <img v-if="program.url" :src="thumb" alt="" />
      <svg v-else viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
    </div>
    <div class="sched-details">
      <span class="sched-title">{{ title }}</span>
      <span class="sched-channel">{{ channelLabel }}</span>
      <span class="sched-time">{{ timeRange }}</span>
      <span v-if="program.genre" class="sched-genre">{{ program.genre }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { minsToTime, cleanTitle, thumbUrl } from '../api.js'

const props = defineProps({
  program: { type: Object, required: true },
  status: { type: String, default: 'future' },
})

const title = computed(() => cleanTitle(props.program.program_id))
const channelLabel = computed(() => props.program.channel_name || `Channel ${props.program.channel_id}`)
const timeRange = computed(() => `${minsToTime(props.program.start)} — ${minsToTime(props.program.end)}`)
const thumb = computed(() => props.program.url ? thumbUrl(props.program.url) : '')
</script>
