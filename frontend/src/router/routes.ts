import type { RouteRecordRaw } from 'vue-router'

export const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/Index.vue'),
    meta: { public: true, title: '登录' },
  },

  // ---------------- mobile (no sidebar) ----------------
  {
    path: '/mobile/inspection',
    component: () => import('@/layout/MobileLayout.vue'),
    meta: { roles: ['admin', 'inspector'] },
    children: [
      {
        path: '',
        name: 'MobileInspectionHome',
        component: () => import('@/views/mobile/InspectionHome.vue'),
        meta: { title: '移动巡检', mobile: true, roles: ['admin', 'inspector'] },
      },
      {
        path: 'rooms/:roomCode/start',
        name: 'MobileInspectionStart',
        component: () => import('@/views/mobile/InspectionStart.vue'),
        meta: { title: '机房巡检', mobile: true, roles: ['admin', 'inspector'] },
      },
      {
        path: 'records/:recordId/equipment/:equipmentId',
        name: 'MobileEquipmentInspect',
        component: () => import('@/views/mobile/EquipmentInspect.vue'),
        meta: { title: '设备巡检', mobile: true, roles: ['admin', 'inspector'] },
      },
      {
        path: 'records/:recordId/confirm',
        name: 'MobileConfirm',
        component: () => import('@/views/mobile/Confirm.vue'),
        meta: { title: '提交确认', mobile: true, roles: ['admin', 'inspector'] },
      },
      {
        path: 'records/:recordId/success',
        name: 'MobileSuccess',
        component: () => import('@/views/mobile/Success.vue'),
        meta: { title: '提交成功', mobile: true, roles: ['admin', 'inspector'] },
      },
    ],
  },

  // ---------------- desktop (with sidebar) ----------------
  {
    path: '/',
    component: () => import('@/layout/BasicLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '首页看板', icon: 'DataLine', parentTitle: '工作台' },
      },
      {
        path: 'inspection/records',
        name: 'InspectionRecords',
        component: () => import('@/views/inspection/RecordList.vue'),
        meta: { title: '巡检记录', icon: 'Document', parentTitle: '巡检管理' },
      },
      {
        path: 'inspection/records/:recordId',
        name: 'InspectionRecordDetail',
        component: () => import('@/views/inspection/RecordDetail.vue'),
        meta: { title: '巡检详情', icon: 'Document', parentTitle: '巡检管理' },
      },
      {
        path: 'issues/:status',
        name: 'IssueList',
        component: () => import('@/views/issue/IssueList.vue'),
        meta: { title: '问题闭环', icon: 'Warning', parentTitle: '问题闭环',
                roles: ['admin', 'handler', 'verifier'] },
      },
      {
        path: 'basic/rooms',
        name: 'Rooms',
        component: () => import('@/views/basic/RoomList.vue'),
        meta: { title: '机房管理', icon: 'OfficeBuilding', parentTitle: '基础信息' },
      },
      {
        path: 'rooms/:roomId/equipment',
        name: 'RoomEquipment',
        component: () => import('@/views/basic/RoomEquipment.vue'),
        meta: { title: '机房设备', icon: 'Cpu', parentTitle: '基础信息' },
      },
      {
        path: 'equipment',
        name: 'Equipment',
        component: () => import('@/views/equipment/EquipmentList.vue'),
        meta: { title: '设备管理', icon: 'Cpu', parentTitle: '基础信息' },
      },
      {
        path: 'system/users',
        name: 'Users',
        component: () => import('@/views/system/UserList.vue'),
        meta: { title: '用户管理', icon: 'User', parentTitle: '系统管理', roles: ['admin'] },
      },
      {
        path: 'system/inspection-qr',
        name: 'InspectionQr',
        component: () => import('@/views/system/InspectionQr.vue'),
        meta: { title: '巡检入口二维码', icon: 'Grid', parentTitle: '系统管理', roles: ['admin'] },
      },
    ],
  },

  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: { public: true },
  },
]

export interface MenuItem {
  title: string
  icon?: string
  path?: string
  roles?: string[]
  children?: MenuItem[]
  disabled?: boolean
  badge?: string
}

export const menu: MenuItem[] = [
  { title: '首页看板', icon: 'DataLine', path: '/dashboard' },
  {
    title: '巡检管理',
    icon: 'Tickets',
    children: [
      { title: '巡检记录', icon: 'Document', path: '/inspection/records' },
    ],
  },
  {
    title: '问题闭环',
    icon: 'Warning',
    roles: ['admin', 'handler', 'verifier'],
    children: [
      { title: '待转发', icon: 'Promotion', path: '/issues/pending_assign', roles: ['admin'] },
      { title: '待处理', icon: 'AlarmClock', path: '/issues/pending_handle', roles: ['admin', 'handler'] },
      { title: '待核实', icon: 'CircleCheck', path: '/issues/pending_verify', roles: ['admin', 'verifier'] },
      { title: '已完成', icon: 'Finished', path: '/issues/completed', roles: ['admin', 'handler', 'verifier'] },
    ],
  },
  {
    title: '基础信息',
    icon: 'Setting',
    children: [
      { title: '机房管理', icon: 'OfficeBuilding', path: '/basic/rooms' },
      { title: '设备管理', icon: 'Cpu', path: '/equipment' },
    ],
  },
  {
    title: '系统管理',
    icon: 'Tools',
    roles: ['admin'],
    children: [
      { title: '用户管理', icon: 'User', path: '/system/users', roles: ['admin'] },
      { title: '巡检入口二维码', icon: 'Grid', path: '/system/inspection-qr', roles: ['admin'] },
    ],
  },
]
