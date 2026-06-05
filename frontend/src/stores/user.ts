import { defineStore } from 'pinia'
import { apiLogin, apiMe, type UserInfo } from '@/api/auth'
import { clearToken, setToken } from '@/utils/auth'

interface State {
  user: UserInfo | null
}

export const useUserStore = defineStore('user', {
  state: (): State => ({
    user: null,
  }),
  getters: {
    role: (s) => s.user?.role ?? '',
    isAdmin: (s) => s.user?.role === 'admin',
  },
  actions: {
    async login(username: string, password: string) {
      const { token, user } = await apiLogin(username, password)
      setToken(token)
      this.user = user
    },
    async fetchMe() {
      this.user = await apiMe()
    },
    logout() {
      clearToken()
      this.user = null
    },
  },
})
