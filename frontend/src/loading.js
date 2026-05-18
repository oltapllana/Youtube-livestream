import { reactive, readonly, ref } from 'vue'

const state = reactive({
  open: false,
  title: 'Loading',
  message: '',
  depth: 0, // e mban overlay hapur nëse ke requests paralel
  remainingSeconds: 0, // sekonda të mbetura (backward countdown)
  estimatedDuration: 30, // estimated duration in seconds
  measuredTime: null, // actual time from last request
  showMeasuredTime: false, // show measured time instead of countdown
})

let timerInterval = null
let startTime = null

export function useLoading() {
  return readonly(state)
}

function startTimer() {
  if (timerInterval) return
  startTime = Date.now()
  state.remainingSeconds = state.estimatedDuration || 0
  
  timerInterval = setInterval(() => {
    if (!state.estimatedDuration) {
      state.remainingSeconds = 0
      return
    }
    const elapsed = Math.floor((Date.now() - startTime) / 1000)
    const remaining = Math.max(0, state.estimatedDuration - elapsed)
    state.remainingSeconds = remaining
  }, 100)
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
    state.remainingSeconds = 0
  }
}

export function showLoader({ title = 'Loading', message = '', estimatedDuration = null } = {}) {
  state.depth += 1
  state.open = true
  state.title = title
  state.message = message
  state.showMeasuredTime = false
  // Only use measured time if we have one from a PREVIOUS run
  // For first run, don't set duration so countdown won't show
  if (state.measuredTime) {
    state.estimatedDuration = estimatedDuration || state.measuredTime
  } else {
    state.estimatedDuration = estimatedDuration || null
  }
  
  if (state.depth === 1) {
    startTimer()
  }
}

export function setMeasuredTime(timeInSeconds) {
  const measured = Math.round(timeInSeconds)
  state.measuredTime = measured
  state.estimatedDuration = measured  // Update default for next run
  console.log(`📊 Measured time: ${measured}s, next countdown will use this`)
}

export function hideLoader() {
  state.depth = Math.max(0, state.depth - 1)
  if (state.depth === 0) {
    state.open = false
    state.message = ''
    state.title = 'Loading'
    stopTimer()
  }
}

/** helper: e mbështjell çdo async function automatikisht */
export async function withLoader(opts, fn) {
  showLoader(opts)
  try {
    return await fn()
  } finally {
    hideLoader()
  }
}
