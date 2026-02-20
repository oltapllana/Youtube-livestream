<template>
  <div class="now-playing-wrap">
    <!-- Progress bar -->
    <div v-if="program" class="np-progress-track">
      <div class="np-progress-bar" :style="{ width: progressPct + '%' }"></div>
    </div>
    <div class="now-playing">
      <div class="np-info">
        <span v-if="program" class="np-live-badge"><span class="np-live-dot"></span>LIVE</span>
        <span class="np-title">{{ title }}</span>
        <span class="np-channel">{{ channel }}</span>
      </div>
      <div class="np-right">
        <div class="np-time">{{ timeRange }}</div>
        <div class="np-countdown">
          <svg class="np-countdown-icon" viewBox="0 0 24 24">
            <path d="M15 1H9v2h6V1zm-4 13h2V8h-2v6zm8.03-6.61l1.42-1.42c-.43-.51-.9-.99-1.41-1.41l-1.42 1.42A8.962 8.962 0 0012 4c-4.97 0-9 4.03-9 9s4.03 9 9 9 9-4.03 9-9c0-2.12-.74-4.07-1.97-5.61zM12 20c-3.87 0-7-3.13-7-7s3.13-7 7-7 7 3.13 7 7-3.13 7-7 7z"/>
          </svg>
          <span class="np-countdown-text">{{ countdown }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { minsToTime, cleanTitle } from '../api.js'

const props = defineProps({
  program: { type: Object, default: null },
  nextProgram: { type: Object, default: null },
})

const countdown = ref('')
const progressPct = ref(0)
let countdownTimer = null

function updateCountdown() {
  if (!props.program) {
    countdown.value = ''
    progressPct.value = 0
    return
  }
  const now = new Date()
  const nowTotalSecs = now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds()
  let startSecs = props.program.start * 60
  let endSecs = props.program.end * 60
  // Handle cross-midnight schedules
  if (endSecs > 86400) endSecs = endSecs // keep as-is (>24h notation)
  let diff = endSecs - nowTotalSecs
  if (diff < -43200) diff += 86400
  // Calculate progress percentage
  const totalDuration = endSecs - startSecs
  const elapsed = nowTotalSecs - startSecs
  if (totalDuration > 0) {
    progressPct.value = Math.min(100, Math.max(0, (elapsed / totalDuration) * 100))
  }
  if (diff <= 0) {
    countdown.value = '0m 00s'
    progressPct.value = 100
    return
  }
  const hrs = Math.floor(diff / 3600)
  const mins = Math.floor((diff % 3600) / 60)
  const secs = diff % 60
  if (hrs > 0) {
    countdown.value = `${hrs}h ${String(mins).padStart(2, '0')}m ${String(secs).padStart(2, '0')}s`
  } else {
    countdown.value = `${mins}m ${String(secs).padStart(2, '0')}s`
  }
}

function startCountdown() {
  if (countdownTimer) clearInterval(countdownTimer)
  updateCountdown()
  countdownTimer = setInterval(updateCountdown, 1000)
}

function stopCountdown() {
  if (countdownTimer) clearInterval(countdownTimer)
  countdownTimer = null
  countdown.value = ''
}

watch(() => props.program, (p) => {
  if (p) startCountdown()
  else stopCountdown()
}, { immediate: true })

onUnmounted(stopCountdown)

const title = computed(() => {
  if (props.program) return props.program.program_name || cleanTitle(props.program.program_id)
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

<style scoped>
.now-playing-wrap {
  border-radius: 0 0 12px 12px;
  overflow: hidden;
  margin-top: -1px;
}
.np-progress-track {
  height: 3px;
  background: rgba(255, 255, 255, 0.08);
  width: 100%;
}
.np-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #3ea6ff, #ff4444);
  border-radius: 0 2px 2px 0;
  transition: width 1s linear;
  position: relative;
}
.np-progress-bar::after {
  content: '';
  position: absolute;
  right: -1px;
  top: -3px;
  width: 9px;
  height: 9px;
  background: #ff4444;
  border-radius: 50%;
  box-shadow: 0 0 6px rgba(255, 68, 68, 0.6);
}
.np-live-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  background: #fff;
  border-radius: 50%;
  margin-right: 4px;
  animation: pulse-dot 1.5s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
.np-right {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}
.np-countdown {
  display: flex;
  align-items: center;
  gap: 5px;
  background: rgba(255, 255, 255, 0.08);
  padding: 4px 10px;
  border-radius: 6px;
  white-space: nowrap;
}
.np-countdown-icon {
  width: 16px;
  height: 16px;
  fill: #ff9800;
  flex-shrink: 0;
}
.np-countdown-text {
  font-size: 14px;
  font-weight: 600;
  color: #ff9800;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.5px;
}
</style>
