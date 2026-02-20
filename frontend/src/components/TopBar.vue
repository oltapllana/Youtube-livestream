<template>
  <header class="topbar">
    <div class="topbar-left">
      <img
        src="../assets/up.svg"
        alt="UniPRStream Logo"
        class="logo-image"
        style="height:40px;background-color:white;border-radius:100%"
      />
      <span class="logo-brand">UniPR<span class="logo-accent">Stream</span></span>
    </div>
    <div class="topbar-center">
      <span class="now-label">{{ clockLabel }}</span>
      <span class="topbar-clock">{{ liveClock }}</span>
    </div>
    <div class="topbar-right">
      <div class="kbd-hints">
        <kbd>F</kbd> <span>Fullscreen</span>
        <kbd>Esc</kbd> <span>Close</span>
      </div>
      <button class="btn-icon" @click="$emit('openPrefs')" title="Preferences">
        <svg viewBox="0 0 24 24">
          <path d="M3 17v2h6v-2H3zM3 5v2h10V5H3zm10 16v-2h8v-2h-8v-2h-2v6h2zM7 9v2H3v2h4v2h2V9H7zm14 4v-2H11v2h10zm-6-4h2V7h4V5h-4V3h-2v6z" />
        </svg>
      </button>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

defineProps({
  clockLabel: { type: String, default: '—' },
})

defineEmits(['openPrefs'])

const liveClock = ref('')
let clockInterval = null

function updateClock() {
  const d = new Date()
  liveClock.value = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

onMounted(() => {
  updateClock()
  clockInterval = setInterval(updateClock, 1000)
})

onUnmounted(() => {
  if (clockInterval) clearInterval(clockInterval)
})
</script>

<style scoped>
.logo-image {
  height: 42px;
  width: auto;
  object-fit: contain;
}
.logo-brand {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.5px;
  color: #f1f1f1;
}
.logo-accent {
  color: #3ea6ff;
}
.topbar-clock {
  display: block;
  font-size: 11px;
  color: #666;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.5px;
  margin-top: 1px;
}
.kbd-hints {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-right: 8px;
  opacity: 0.4;
  transition: opacity 0.2s;
}
.kbd-hints:hover {
  opacity: 0.8;
}
.kbd-hints kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 20px;
  padding: 0 5px;
  background: #272727;
  border: 1px solid #444;
  border-radius: 4px;
  font-size: 10px;
  font-family: inherit;
  color: #ccc;
  line-height: 1;
}
.kbd-hints span {
  font-size: 10px;
  color: #888;
  margin-right: 6px;
}
@media(max-width: 768px) {
  .kbd-hints { display: none; }
  .topbar-clock { display: none; }
}
</style>