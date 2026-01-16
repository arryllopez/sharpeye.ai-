"use client"

import { PlayerPropsView } from "@/components/player-props-view"
import { useParams, useSearchParams } from "next/navigation"

export default function GamePage() {
  const params = useParams()
  const searchParams = useSearchParams()

  const gameId = params.id as string
  const homeTeam = searchParams.get("home") || undefined
  const awayTeam = searchParams.get("away") || undefined
  const gameTime = searchParams.get("time") || undefined

  return (
    <main className="min-h-screen bg-background pt-20">
      <PlayerPropsView
        gameId={gameId}
        homeTeam={homeTeam}
        awayTeam={awayTeam}
        gameTime={gameTime}
      />
    </main>
  )
}
