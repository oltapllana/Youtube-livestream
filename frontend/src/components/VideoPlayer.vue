<template>
  <div class="player-wrap" ref="wrapRef">
    <!-- Placeholder: no program playing -->
    <div v-if="!program" class="player-placeholder">
      <!-- Loading -->
      <template v-if="loading">
        <div class="spinner"></div>
        <p>{{ loadingMsg }}</p>
      </template>

      <!-- No schedule generated yet -->
   <template v-else-if="!hasSchedule">
  <div class="spinner"></div>
</template>


      <!-- Waiting for next program -->
      <template v-else-if="nextProgram">
        <svg viewBox="0 0 24 24" class="play-big">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14V8l5 4-5 4z" />
        </svg>
        <p>Next up at <strong>{{ minsToTime(nextProgram.start) }}</strong></p>
        <p class="sub-text">{{ cleanTitle(nextProgram.program_id) }} — Channel {{ nextProgram.channel_id }}</p>
      </template>

      <!-- Schedule ended -->
      <template v-else>
        <svg viewBox="0 0 24 24" class="play-big">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
        </svg>
        <p>Today's schedule has ended</p>
        <p class="sub-text">Open preferences to generate a new schedule</p>
      </template>
    </div>

    <!-- Active YouTube player -->
    <div v-else class="player-container">
      <iframe
        :src="embedUrl(program.url)"
        frameborder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen"
        allowfullscreen
      ></iframe>
    </div>

    <!-- Fullscreen toggle -->
    <button class="btn-fullscreen" @click="toggleFullscreen" title="Toggle fullscreen">
      <svg viewBox="0 0 24 24">
        <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { minsToTime, cleanTitle, embedUrl } from '../api.js'

defineProps({
  program: { type: Object, default: null },
  nextProgram: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  loadingMsg: { type: String, default: '' },
  hasSchedule: { type: Boolean, default: false },
})

const wrapRef = ref(null)

function toggleFullscreen() {
  const el = wrapRef.value
  if (!el) return
  if (!document.fullscreenElement) {
    el.requestFullscreen().catch(() => el.classList.toggle('is-fullscreen'))
  } else {
    document.exitFullscreen()
  }
}

function onFsChange() {
  if (wrapRef.value) {
    wrapRef.value.classList.toggle('is-fullscreen', !!document.fullscreenElement)
  }
}

onMounted(() => document.addEventListener('fullscreenchange', onFsChange))
onUnmounted(() => document.removeEventListener('fullscreenchange', onFsChange))
</script>
<style scoped>
.spinner{
  width: 42px;
  height: 42px;
  border-radius: 999px;
  border: 3px solid rgba(255,255,255,.18);
  border-top-color: rgba(255,255,255,.92);
  animation: spin 1s linear infinite;
  margin: 0 auto 10px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>