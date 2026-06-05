import type { Router } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getToken } from '@/utils/auth'

/** Allow only same-origin redirects that start with `/` and don't look like a protocol-relative URL. */
export function sanitizeRedirect(raw: unknown): string | null {
  if (typeof raw !== 'string') return null
  const v = raw.trim()
  if (!v.startsWith('/')) return null
  if (v.startsWith('//')) return null
  if (/^\/\\/.test(v)) return null
  // disallow protocol injection
  if (/^\/[a-z][a-z0-9+.-]*:/i.test(v)) return null
  return v
}

/** 手机/微信等移动端设备。手机端只做巡检，不展示后台管理界面。 */
export function isMobileDevice(): boolean {
  if (typeof navigator === 'undefined') return false
  return /Android|iPhone|iPad|iPod|Mobile|MicroMessenger/i.test(navigator.userAgent)
}

const MOBILE_HOME = '/mobile/inspection'

/** 可进行巡检的角色（手机端入口只对这些角色有意义）。 */
function canInspect(role: string): boolean {
  return role === 'admin' || role === 'inspector'
}

export function registerGuards(router: Router) {
  router.beforeEach(async (to) => {
    const userStore = useUserStore()
    const token = getToken()

    if (to.meta.public) {
      if (to.name === 'Login' && token && userStore.user) {
        const r = sanitizeRedirect(to.query.redirect)
        // 手机端可巡检角色：默认进巡检首页，不进后台
        if (isMobileDevice() && canInspect(userStore.role) && (!r || !r.startsWith('/mobile'))) {
          return { path: MOBILE_HOME }
        }
        return { path: r ?? '/dashboard' }
      }
      return true
    }

    if (!token) {
      return {
        name: 'Login',
        query: { redirect: to.fullPath },
      }
    }

    if (!userStore.user) {
      try {
        await userStore.fetchMe()
      } catch {
        userStore.logout()
        return { name: 'Login', query: { redirect: to.fullPath } }
      }
    }

    // 手机端只走移动巡检：可巡检角色访问任何后台页都导回巡检首页（手机端不展示后台管理）
    if (isMobileDevice() && canInspect(userStore.role) && !to.path.startsWith('/mobile')) {
      return { path: MOBILE_HOME }
    }

    const requiredRoles = to.meta.roles as string[] | undefined
    if (requiredRoles && requiredRoles.length && !requiredRoles.includes(userStore.role)) {
      return { path: '/dashboard' }
    }

    return true
  })

  router.afterEach((to) => {
    const baseTitle = import.meta.env.VITE_APP_TITLE || '机房巡检系统'
    if (to.meta.title) {
      document.title = `${to.meta.title} | ${baseTitle}`
    } else {
      document.title = baseTitle
    }
  })
}
