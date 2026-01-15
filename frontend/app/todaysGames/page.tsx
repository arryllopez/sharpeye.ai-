import { TodaysGames } from "@/components/todays-games"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"

export const metadata = {
  title: "Today's Games | sharpeye.io",
  description: "View today's games with player prop insights and model edges.",
}

export default function GamesPage() {
  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto max-w-6xl px-6 py-8">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-8"
        >
          <ArrowLeft className="size-4" />
          Back to Home
        </Link>
      </div>
      <TodaysGames />
    </main>
  )
}
