import { reactive, readonly } from 'vue'

const state = reactive({
  open: false,
  title: 'Loading',
  message: '',
  depth: 0, // e mban overlay hapur nëse ke requests paralel
})

export function useLoading() {
  return readonly(state)
}

export function showLoader({ title = 'Loading', message = '' } = {}) {
  state.depth += 1
  state.open = true
  state.title = title
  state.message = message
}

export function hideLoader() {
  state.depth = Math.max(0, state.depth - 1)
  if (state.depth === 0) {
    state.open = false
    state.message = ''
    state.title = 'Loading'
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
