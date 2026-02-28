import { ReactNode } from 'react'

interface RFQLayoutProps {
  children: ReactNode
}

export default function RFQLayout({ children }: RFQLayoutProps) {
  return <>{children}</>
}
