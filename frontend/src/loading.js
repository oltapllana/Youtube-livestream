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
  
  // Use measured time from previous run, or estimate based on context
  if (state.measuredTime) {
    // Use actual time from last run
    state.estimatedDuration = estimatedDuration || state.measuredTime
  } else {
    // First run or no data: use reasonable default (20 seconds)
    state.estimatedDuration = estimatedDuration || 20
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
    // Measure actual elapsed time and use it for next countdown
    if (startTime) {
      const actualElapsed = Math.round((Date.now() - startTime) / 1000)
      if (actualElapsed > 0) {
        console.log(`⏱️ Actual execution: ${actualElapsed}s`)
        setMeasuredTime(actualElapsed)
      }
    }
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
  } catch (error) {
    console.error('Error during loading:', error)
    throw error
  } finally {
    hideLoader()
  }
}
