<template>
  <div>
    <!-- Overlay -->
    <div class="filters-overlay" :class="{ open }" @click="$emit('update:open', false)"></div>

    <!-- Panel -->
    <aside class="filters-panel" :class="{ open }">
    <div class="filters-header">
      <h2>Preferences</h2>
      <button class="btn-icon btn-close" @click="$emit('update:open', false)">&times;</button>
    </div>

    <div class="filters-body">
      <label>
        <span>Opening Time</span>
        <input type="time" v-model="prefs.openTime" />
      </label>
      <label>
        <span>Closing Time</span>
        <input type="time" v-model="prefs.closeTime" />
      </label>
      <label>
        <span>Min Duration (% of shortest)</span>
        <select v-model.number="prefs.minDurationPct">
          <option :value="70">70%</option>
          <option :value="80">80%</option>
          <option :value="90">90%</option>
          <option :value="100">100%</option>
        </select>
      </label>
      <label>
        <span>Channels Count</span>
        <select v-model.number="prefs.channelsCount">
          <option :value="10">10</option>
          <option :value="20">20</option>
        </select>
      </label>
      <label>
        <span>Switch Penalty (% of avg score)</span>
        <select v-model.number="prefs.switchPenaltyPct">
          <option :value="3">3%</option>
          <option :value="5">5%</option>
          <option :value="7">7%</option>
          <option :value="10">10%</option>
        </select>
      </label>
      <label>
        <span>Bonus (% of avg score)</span>
        <select v-model.number="prefs.bonusPct">
          <option :value="3">3%</option>
          <option :value="5">5%</option>
          <option :value="7">7%</option>
          <option :value="10">10%</option>
        </select>
      </label>
      <label>
        <span>Termination Penalty</span>
        <input type="number" v-model.number="prefs.terminationPenalty" min="0" max="100" />
      </label>
      <label>
        <span>Max Consecutive Genre</span>
        <input type="number" v-model.number="prefs.maxConsecutiveGenre" min="1" max="10" />
      </label>

      <div class="filters-actions">
        <button class="btn btn-secondary" @click="onSave">Save</button>
        <button class="btn btn-primary" @click="$emit('saveAndGenerate')">Save &amp; Generate</button>
      </div>
      <p class="filters-status" :style="{ color: statusColor }">{{ statusMsg }}</p>
    </div>
  </aside>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  prefs: { type: Object, required: true },
})

const emit = defineEmits(['update:open', 'save', 'saveAndGenerate'])

const statusMsg = ref('')
const statusColor = ref('#aaa')

async function onSave() {
  try {
    const ok = await new Promise((resolve) => {
      // Parent returns the result via the emit
      emit('save')
      // We'll assume success for now — parent handles API call
      resolve(true)
    })
    statusMsg.value = 'Preferences saved!'
    statusColor.value = '#4caf50'
  } catch {
    statusMsg.value = 'Failed to save'
    statusColor.value = '#f44336'
  }
  setTimeout(() => { statusMsg.value = '' }, 3000)
}
</script>
