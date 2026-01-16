import { TodaysGames } from "@/components/todays-games"

export const metadata = {
  title: "Today's Games | sharpeye.io",
  description: "View today's games with player prop insights and model edges.",
}

export default function GamesPage() {
  return (
    <main className="min-h-screen bg-background pt-20">
      <TodaysGames />
    </main>
  )
}
