<template>
  <div>
    <TopBar :clock-label="clockLabel" @open-prefs="showPrefs = true" />

    <PreferencesPanel
      v-model:open="showPrefs"
      :prefs="prefs"
      @save="onSavePrefs"
      @save-and-generate="onSaveAndGenerate"
    />

    <main class="main">
      <section class="player-section">
        <VideoPlayer
          :program="currentProg"
          :next-program="nextProg"
          :loading="loading"
          :loading-msg="loadingMsg"
          :has-schedule="schedule.length > 0"
        />
        <NowPlaying
          :program="currentProg"
          :next-program="nextProg"
        />
      </section>

      <section class="schedule-section">
        <h3 class="section-title">Schedule</h3>
        <ScheduleList
          :schedule="schedule"
          :now="clockNow"
          :loading="loading"
        />
      </section>
    </main>

    <LoadingOverlay v-if="loading" :message="loadingMsg" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import {
  minsToTime,
  timeToMins,
  getNowMins,
  cleanTitle,
  fetchPreferences,
  savePreferences as apiSavePrefs,
  generateSchedule as apiGenerate,
} from './api.js'

import TopBar from './components/TopBar.vue'
import PreferencesPanel from './components/PreferencesPanel.vue'
import VideoPlayer from './components/VideoPlayer.vue'
import NowPlaying from './components/NowPlaying.vue'
import ScheduleList from './components/ScheduleList.vue'
import LoadingOverlay from './components/LoadingOverlay.vue'

// ── State ────────────────────────────────────────────────────
const showPrefs  = ref(false)
const loading    = ref(false)
const loadingMsg = ref('Generating schedule…')
const schedule   = ref([])
const clockNow   = ref(getNowMins())
const scheduleClosingTime = ref(null) // Track when current schedule ends

const prefs = ref({
  openTime: '08:00',
  closeTime: '23:00',
  minDurationPct: 100,
  channelsCount: 10,
  switchPenaltyPct: 10,
  terminationPenalty: 20,
  maxConsecutiveGenre: 2,
  bonusPct: 5,
})

let clockTimer = null

// ── Computed: time-aware program lookup ──────────────────────
const currentProg = computed(() => {
  const now = clockNow.value
  return schedule.value.find((p) => now >= p.start && now < p.end) || null
})

const nextProg = computed(() => {
  const now = clockNow.value
  return schedule.value.find((p) => p.start > now) || null
})

const clockLabel = computed(() => {
  if (currentProg.value) return `Now playing: ${cleanTitle(currentProg.value.program_id)}`
  if (nextProg.value) return `Next at ${minsToTime(nextProg.value.start)}`
  return minsToTime(clockNow.value)
})

// ── Build payload from prefs ─────────────────────────────────
function buildPayload() {
  return {
    opening_time: timeToMins(prefs.value.openTime),
    closing_time: timeToMins(prefs.value.closeTime),
    min_duration_pct: prefs.value.minDurationPct,
    channels_count: prefs.value.channelsCount,
    switch_penalty_pct: prefs.value.switchPenaltyPct,
    termination_penalty: prefs.value.terminationPenalty,
    max_consecutive_genre: prefs.value.maxConsecutiveGenre,
    time_preferences: [],
    bonus_pct: prefs.value.bonusPct,
  }
}

// ── Build default payload with dynamic time window ───────────
function buildAutoPayload(openTime, closeTime) {
  return {
    opening_time: openTime,
    closing_time: closeTime,
    min_duration_pct: 100,        // defaults
    channels_count: 10,
    switch_penalty_pct: 10,
    termination_penalty: 20,
    max_consecutive_genre: 2,
    time_preferences: [],
    bonus_pct: 5,
  }
}

// ── Load prefs from API ──────────────────────────────────────
async function loadPreferences() {
  try {
    const data = await fetchPreferences()
    prefs.value.openTime = minsToTime(data.opening_time ?? 480)
    prefs.value.closeTime = minsToTime(data.closing_time ?? 1380)
    prefs.value.minDurationPct = data.min_duration_pct ?? 100
    prefs.value.channelsCount = data.channels_count ?? 10
    prefs.value.switchPenaltyPct = data.switch_penalty_pct ?? 10
    prefs.value.terminationPenalty = data.termination_penalty ?? 20
    prefs.value.maxConsecutiveGenre = data.max_consecutive_genre ?? 2
    prefs.value.bonusPct = data.bonus_pct ?? 5
  } catch (e) {
    console.warn('Could not load preferences:', e)
  }
}

// ── Generate schedule ────────────────────────────────────────
async function runGenerate(customPayload = null) {
  loading.value = true
  loadingMsg.value = 'Generating schedule — running beam search algorithm…'
  try {
    const payload = customPayload || buildPayload()
    const data = await apiGenerate(payload)
    schedule.value = data.scheduled_programs || []
    
    // Track closing time from the payload used
    scheduleClosingTime.value = payload.closing_time
    
    // Update prefs UI to reflect what's currently scheduled
    prefs.value.openTime = minsToTime(payload.opening_time)
    prefs.value.closeTime = minsToTime(payload.closing_time)
  } catch (err) {
    console.error('Schedule generation failed:', err)
    alert('Error: ' + err.message)
  } finally {
    loading.value = false
  }
}

// ── Auto-regenerate when schedule expires ────────────────────
async function autoRegenerate() {
  const now = getNowMins()
  const openTime = now
  const closeTime = now + 720 // 12 hours later
  
  console.log(`[AUTO-REGENERATE] Schedule ended. Starting new 12-hour window: ${minsToTime(openTime)} → ${minsToTime(closeTime)}`)
  
  await runGenerate(buildAutoPayload(openTime, closeTime))
}

// ── Panel actions ────────────────────────────────────────────
async function onSavePrefs() {
  return await apiSavePrefs(buildPayload())
}

async function onSaveAndGenerate() {
  await apiSavePrefs(buildPayload())
  showPrefs.value = false
  await runGenerate()
}

// ── Lifecycle ────────────────────────────────────────────────
onMounted(async () => {
  // 1. Load saved preferences
  await loadPreferences()
  // 2. Generate schedule immediately using those prefs
  await runGenerate()
  // 3. Clock tick every 5 seconds for time-aware sync
  clockTimer = setInterval(() => {
    clockNow.value = getNowMins()
  }, 5000)

  document.addEventListener('keydown', onKeydown)
})

// ── Watch for schedule expiration ────────────────────────────
watch(clockNow, (now) => {
  // If current time exceeds schedule closing time, auto-regenerate
  if (scheduleClosingTime.value !== null && now >= scheduleClosingTime.value && !loading.value) {
    autoRegenerate()
  }
})

onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer)
  document.removeEventListener('keydown', onKeydown)
})

function onKeydown(e) {
  if (e.key === 'Escape') {
    if (showPrefs.value) showPrefs.value = false
    if (document.fullscreenElement) document.exitFullscreen()
  }
  if (e.key === 'f' && !e.ctrlKey && !e.metaKey) {
    const tag = document.activeElement.tagName
    if (tag !== 'INPUT' && tag !== 'TEXTAREA') {
      const wrap = document.querySelector('.player-wrap')
      if (!document.fullscreenElement) {
        wrap?.requestFullscreen().catch(() => wrap?.classList.toggle('is-fullscreen'))
      } else {
        document.exitFullscreen()
      }
    }
  }
}
</script>
