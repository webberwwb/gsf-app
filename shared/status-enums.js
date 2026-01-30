/**
 * Status Enums - Single Source of Truth
 * All status values and labels for the entire application
 * 
 * This file is shared between app and admin frontends
 * Keep in sync with backend/constants/status_enums.py
 */

/**
 * Order Status Enum
 * Workflow: submitted → confirmed → preparing → ready_for_pickup/out_for_delivery → completed
 * Can be cancelled at any stage
 */
export const OrderStatus = {
  SUBMITTED: 'submitted',           // 已提交订单 - User placed order, can edit/cancel
  CONFIRMED: 'confirmed',           // 已确认订单 - Order deadline passed, user cannot edit products but can edit pickup/payment
  PREPARING: 'preparing',           // 正在配货 - Admin started preparing
  PACKING_COMPLETE: 'packing_complete',  // 配货完成 - Packing completed, ready for next step
  READY_FOR_PICKUP: 'ready_for_pickup',  // 可以取货 - Ready for customer pickup
  OUT_FOR_DELIVERY: 'out_for_delivery',  // 正在配送 - Out for delivery (delivery orders only)
  COMPLETED: 'completed',           // 订单完成 - Order completed and paid
  CANCELLED: 'cancelled',           // 已取消 - Order cancelled
}

export const OrderStatusLabels = {
  [OrderStatus.SUBMITTED]: '已提交订单',
  [OrderStatus.CONFIRMED]: '已确认订单',
  [OrderStatus.PREPARING]: '正在配货',
  [OrderStatus.PACKING_COMPLETE]: '配货完成',
  [OrderStatus.READY_FOR_PICKUP]: '可以取货',
  [OrderStatus.OUT_FOR_DELIVERY]: '正在配送',
  [OrderStatus.COMPLETED]: '订单完成',
  [OrderStatus.CANCELLED]: '已取消',
}

export function getOrderStatusLabel(status) {
  return OrderStatusLabels[status] || status
}

export function isOrderEditableByUser(status) {
  return status === OrderStatus.SUBMITTED
}

export function isOrderCancellableByUser(status) {
  return status === OrderStatus.SUBMITTED
}

/**
 * Payment Status Enum
 */
export const PaymentStatus = {
  UNPAID: 'unpaid',  // 未付款
  PAID: 'paid',      // 已付款
}

export const PaymentStatusLabels = {
  [PaymentStatus.UNPAID]: '未付款',
  [PaymentStatus.PAID]: '已付款',
}

export function getPaymentStatusLabel(status) {
  return PaymentStatusLabels[status] || status
}

/**
 * Group Deal Status Enum
 * Manual: draft (admin-only, not visible to users)
 * Auto-managed: upcoming → active → closed (by cron job based on dates)
 * Manual: preparing → ready_for_pickup → completed (by admin)
 */
export const GroupDealStatus = {
  DRAFT: 'draft',                   // 草稿 - Draft (admin-only, not visible to users)
  UPCOMING: 'upcoming',             // 即将开始 - Before order_start_date (auto)
  ACTIVE: 'active',                 // 进行中 - Between order dates (auto)
  CLOSED: 'closed',                 // 已截单 - After order_end_date (auto)
  PREPARING: 'preparing',           // 正在配货 - Admin started preparing (manual)
  READY_FOR_PICKUP: 'ready_for_pickup',  // 可以取货 - Ready for pickup (manual)
  COMPLETED: 'completed',           // 已完成 - All done (manual)
}

export const GroupDealStatusLabels = {
  [GroupDealStatus.DRAFT]: '草稿',
  [GroupDealStatus.UPCOMING]: '即将开始',
  [GroupDealStatus.ACTIVE]: '进行中',
  [GroupDealStatus.CLOSED]: '已截单',
  [GroupDealStatus.PREPARING]: '正在配货',
  [GroupDealStatus.READY_FOR_PICKUP]: '可以取货',
  [GroupDealStatus.COMPLETED]: '已完成',
}

export function getGroupDealStatusLabel(status) {
  return GroupDealStatusLabels[status] || status
}

export function isGroupDealAutoManaged(status) {
  return [
    GroupDealStatus.UPCOMING,
    GroupDealStatus.ACTIVE,
    GroupDealStatus.CLOSED
  ].includes(status)
}

export function isGroupDealManualManaged(status) {
  return [
    GroupDealStatus.DRAFT,
    GroupDealStatus.PREPARING,
    GroupDealStatus.READY_FOR_PICKUP,
    GroupDealStatus.COMPLETED
  ].includes(status)
}

export function isGroupDealVisibleToUsers(status) {
  return status !== GroupDealStatus.DRAFT
}

export const GroupDealAutoManagedStatuses = [
  GroupDealStatus.UPCOMING,
  GroupDealStatus.ACTIVE,
  GroupDealStatus.CLOSED
]

export const GroupDealManualManagedStatuses = [
  GroupDealStatus.DRAFT,
  GroupDealStatus.PREPARING,
  GroupDealStatus.READY_FOR_PICKUP,
  GroupDealStatus.COMPLETED
]

/**
 * Get all valid order statuses
 */
export function getAllOrderStatuses() {
  return Object.values(OrderStatus)
}

/**
 * Get all valid payment statuses
 */
export function getAllPaymentStatuses() {
  return Object.values(PaymentStatus)
}

/**
 * Get all valid group deal statuses
 */
export function getAllGroupDealStatuses() {
  return Object.values(GroupDealStatus)
}

/**
 * User Status Enum
 */
export const UserStatus = {
  ACTIVE: 'active',  // 活跃
  BANNED: 'banned',  // 已禁用
}

export const UserStatusLabels = {
  [UserStatus.ACTIVE]: '活跃',
  [UserStatus.BANNED]: '已禁用',
}

export function getUserStatusLabel(status) {
  return UserStatusLabels[status] || status
}

/**
 * Get all valid user statuses
 */
export function getAllUserStatuses() {
  return Object.values(UserStatus)
}

/**
 * Delivery Method Enum
 */
export const DeliveryMethod = {
  PICKUP: 'pickup',      // 自取
  DELIVERY: 'delivery',  // 配送
}

export const DeliveryMethodLabels = {
  [DeliveryMethod.PICKUP]: '自取',
  [DeliveryMethod.DELIVERY]: '配送',
}

export function getDeliveryMethodLabel(method) {
  return DeliveryMethodLabels[method] || method
}

/**
 * Get all valid delivery methods
 */
export function getAllDeliveryMethods() {
  return Object.values(DeliveryMethod)
}

