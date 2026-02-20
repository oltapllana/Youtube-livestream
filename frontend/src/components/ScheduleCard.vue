<template>
  <div class="sched-card" :class="status" :style="{ animationDelay: (index * 50) + 'ms' }">
    <div class="sched-thumb">
      <img v-if="program.url" :src="thumb" alt="" />
      <svg v-else viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
      <div class="thumb-overlay">
        <div class="thumb-channel">{{ channelLabel }}</div>
      </div>
      <span v-if="duration" class="sched-duration">{{ duration }}</span>
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
  index: { type: Number, default: 0 },
})

const title = computed(() => props.program.program_name || cleanTitle(props.program.program_id))
const channelLabel = computed(() => props.program.channel_name || `Channel ${props.program.channel_id}`)
const timeRange = computed(() => `${minsToTime(props.program.start)} — ${minsToTime(props.program.end)}`)
const thumb = computed(() => props.program.url ? thumbUrl(props.program.url) : '')
const duration = computed(() => {
  const mins = props.program.end - props.program.start
  if (mins <= 0) return ''
  if (mins < 60) return `${mins}m`
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return m > 0 ? `${h}h ${m}m` : `${h}h`
})
</script>

<style scoped>
.thumb-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.85), transparent);
  padding: 20px 6px 4px 6px;
  pointer-events: none;
}
.thumb-channel {
  font-size: 11px;
  font-weight: 600;
  color: #f1f1f1;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sched-duration {
  position: absolute;
  bottom: 4px;
  right: 4px;
  background: rgba(0, 0, 0, 0.8);
  color: #f1f1f1;
  font-size: 11px;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 3px;
  letter-spacing: 0.3px;
  font-variant-numeric: tabular-nums;
}
</style>
