'use client'

import Badge from '@/components/ui/Badge'
import type { ArmVerifyResponse } from '@/lib/api'

interface KleidiaiBadgeProps {
  arm: ArmVerifyResponse | null
}

export default function KleidiaiBadge({ arm }: KleidiaiBadgeProps) {
  if (!arm) {
    return <Badge text="—" color="neutral" />
  }
  if (arm.status === 'pass') {
    return <Badge text={`ON ${arm.arm_arch || ''}`} color="success" />
  }
  if (arm.kleidiai_build) {
    return <Badge text="Partial" color="warning" />
  }
  return <Badge text="OFF" color="danger" />
}
