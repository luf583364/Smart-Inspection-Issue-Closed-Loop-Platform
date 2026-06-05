import { defineStore } from 'pinia'

interface State {
  sideCollapsed: boolean
}

export const useAppStore = defineStore('app', {
  state: (): State => ({
    sideCollapsed: false,
  }),
  actions: {
    toggleSide() {
      this.sideCollapsed = !this.sideCollapsed
    },
  },
})
