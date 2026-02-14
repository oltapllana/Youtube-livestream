<template>
  <div class="schedule-list">
    <p v-if="schedule.length === 0" class="empty-msg">
      {{ loading ? 'Generating schedule…' : 'No schedule yet.' }}
    </p>
    <ScheduleCard
      v-for="(p, i) in schedule"
      :key="i"
      :program="p"
      :status="cardStatus(p)"
      :id="'sched-' + i"
    />
  </div>
</template>

<script setup>
import ScheduleCard from './ScheduleCard.vue'

const props = defineProps({
  schedule: { type: Array, default: () => [] },
  now: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
})

function cardStatus(p) {
  if (p.end <= props.now) return 'past'
  if (props.now >= p.start && props.now < p.end) return 'active'
  return 'future'
}
</script>
