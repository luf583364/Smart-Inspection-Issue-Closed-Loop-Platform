import { createRouter, createWebHashHistory } from 'vue-router'
import { routes } from './routes'
import { registerGuards } from './guards'

export const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

registerGuards(router)

export default router
