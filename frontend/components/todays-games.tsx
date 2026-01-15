"use client"
import React from "react"
import { motion } from "motion/react"
import { ChevronRight, Clock } from "lucide-react"
import Link from "next/link"
import { Button } from "./ui/button"

import { cn } from "@/lib/utils"

import { AnimatedGroup } from "@/components/ui/animated-group"

//  This page displays the data returned from the getting games endpoint 
//  - It defines the types returned from the API endpoint
//  - utilizes fetch to input dynamic data
type ApiGame = {
  event_id : string;
  commence_time : string;
  home_team : string;
  away_team : string;
}

type FrontendGame = {
  id: string,
  time: string,
  status: "upcoming",
  homeTeam: {
    name: string,
    abbr: string,
  },
  awayTeam: {
    name: string,
    abbr: string,
  }
}

const teamLogos: Record<string, string> = {
  ATL: "https://cdn.nba.com/logos/nba/1610612737/global/L/logo.svg",
  BOS: "https://cdn.nba.com/logos/nba/1610612738/global/L/logo.svg",
  BKN: "https://cdn.nba.com/logos/nba/1610612751/global/L/logo.svg",
  CHA: "https://cdn.nba.com/logos/nba/1610612766/global/L/logo.svg",
  CHI: "https://cdn.nba.com/logos/nba/1610612741/global/L/logo.svg",
  CLE: "https://cdn.nba.com/logos/nba/1610612739/global/L/logo.svg",
  DAL: "https://cdn.nba.com/logos/nba/1610612742/global/L/logo.svg",
  DEN: "https://cdn.nba.com/logos/nba/1610612743/global/L/logo.svg",
  DET: "https://cdn.nba.com/logos/nba/1610612765/global/L/logo.svg",
  GSW: "https://cdn.nba.com/logos/nba/1610612744/global/L/logo.svg",
  HOU: "https://cdn.nba.com/logos/nba/1610612745/global/L/logo.svg",
  IND: "https://cdn.nba.com/logos/nba/1610612754/global/L/logo.svg",
  LAC: "https://cdn.nba.com/logos/nba/1610612746/global/L/logo.svg",
  LAL: "https://cdn.nba.com/logos/nba/1610612747/global/L/logo.svg",
  MEM: "https://cdn.nba.com/logos/nba/1610612763/global/L/logo.svg",
  MIA: "https://cdn.nba.com/logos/nba/1610612748/global/L/logo.svg",
  MIL: "https://cdn.nba.com/logos/nba/1610612749/global/L/logo.svg",
  MIN: "https://cdn.nba.com/logos/nba/1610612750/global/L/logo.svg",
  NOP: "https://cdn.nba.com/logos/nba/1610612740/global/L/logo.svg",
  NYK: "https://cdn.nba.com/logos/nba/1610612752/global/L/logo.svg",
  OKC: "https://cdn.nba.com/logos/nba/1610612760/global/L/logo.svg",
  ORL: "https://cdn.nba.com/logos/nba/1610612753/global/L/logo.svg",
  PHI: "https://cdn.nba.com/logos/nba/1610612755/global/L/logo.svg",
  PHX: "https://cdn.nba.com/logos/nba/1610612756/global/L/logo.svg",
  POR: "https://cdn.nba.com/logos/nba/1610612757/global/L/logo.svg",
  SAC: "https://cdn.nba.com/logos/nba/1610612758/global/L/logo.svg",
  SAS: "https://cdn.nba.com/logos/nba/1610612759/global/L/logo.svg",
  TOR: "https://cdn.nba.com/logos/nba/1610612761/global/L/logo.svg",
  UTA: "https://cdn.nba.com/logos/nba/1610612762/global/L/logo.svg",
  WAS: "https://cdn.nba.com/logos/nba/1610612764/global/L/logo.svg",
};


const transitionVariants = {
  container: {
    visible: {
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  },
  item: {
    hidden: {
      opacity: 0,
      y: 20,
      filter: "blur(8px)",
    },
    visible: {
      opacity: 1,
      y: 0,
      filter: "blur(0px)",
      transition: {
        type: "spring",
        bounce: 0.3,
        duration: 0.8,
      },
    },
  },
}

const cardAnimation = {
  hover: {
    scale: 1.02,
    transition: { duration: 0.3 },
  },
}

const imageAnimation = {
  hover: {
    scale: 1.15,
    rotate: 5,
    x: 10,
    transition: { duration: 0.4, ease: "easeInOut" },
  },
}

const arrowAnimation = {
  hover: {
    x: 5,
    transition: {
      duration: 0.3,
      ease: "easeInOut",
      repeat: Number.POSITIVE_INFINITY,
      repeatType: "reverse" as const,
    },
  },
}

export function TodaysGames() {
  const [games, setGames] = React.useState<FrontendGame[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);                      
  const getTeamAbbr = (teamName: string): string => {
  const nameLower = teamName.toLowerCase().trim();
  
  return {
    'boston celtics': 'BOS',
    'new york knicks': 'NYK',
    'brooklyn nets': 'BKN',
    'philadelphia 76ers': 'PHI',
    'toronto raptors': 'TOR',
    'chicago bulls': 'CHI',
    'cleveland cavaliers': 'CLE',
    'detroit pistons': 'DET',
    'indiana pacers': 'IND',
    'milwaukee bucks': 'MIL',
    'atlanta hawks': 'ATL',
    'charlotte hornets': 'CHA',
    'miami heat': 'MIA',
    'orlando magic': 'ORL',
    'washington wizards': 'WAS',
    'denver nuggets': 'DEN',
    'minnesota timberwolves': 'MIN',
    'oklahoma city thunder': 'OKC',
    'portland trail blazers': 'POR',
    'utah jazz': 'UTA',
    'golden state warriors': 'GSW',
    'los angeles clippers': 'LAC',
    'los angeles lakers': 'LAL',
    'phoenix suns': 'PHX',
    'sacramento kings': 'SAC',
    'dallas mavericks': 'DAL',
    'houston rockets': 'HOU',
    'memphis grizzlies': 'MEM',
    'new orleans pelicans': 'NOP',
    'san antonio spurs': 'SAS'
  }[nameLower] || 'UNK'; 
};

  React.useEffect(() => {
    async function fetchGames() {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);

      try {
        setLoading(true);
        setError(null);

        const apiUrl = process.env.NEXT_PUBLIC_API_URL;
        if (!apiUrl) {
          throw new Error("API URL is not configured");
        }

        const response = await fetch(`${apiUrl}/nba/games`, {
          signal: controller.signal
        });
        clearTimeout(timeoutId);

        if (!response.ok) {
          throw new Error(`Failed to fetch games: ${response.status}`);
        }

        const apiGames: ApiGame[] = await response.json();

        const transformedGames: FrontendGame[] = apiGames.map((game) => {
          const commenceDate = new Date(game.commence_time);
          const timeStr = commenceDate.toLocaleTimeString("en-US", {
            hour: "numeric",
            minute: "2-digit",
            timeZone: "America/New_York",
          }) + " ET";
          return {
            id: game.event_id,
            time: timeStr,
            status: "upcoming" as const,
            homeTeam: {
              name: game.home_team,
              abbr: getTeamAbbr(game.home_team),
            },
            awayTeam: {
              name: game.away_team,
              abbr: getTeamAbbr(game.away_team),
            },
          };
        });

        setGames(transformedGames);
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') {
          setError("Request timed out. Please try again.");
        } else {
          setError(err instanceof Error ? err.message : "Failed to load games");
        }
        console.error("Games fetch error:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchGames();
  }, []);

  // Loading state (keeps your animations smooth)
  if (loading) {
    return (
      <section id="games" className="bg-muted/30 py-16 md:py-24">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-medium tracking-tight sm:text-4xl">Today's Games</h2>
            <p className="mt-4 text-muted-foreground">Loading matchups...</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {Array(4).fill(0).map((_, i) => (
              <div key={i} className="animate-pulse bg-muted rounded-xl h-[180px]" />
            ))}
          </div>
        </div>
      </section>
    );
  }

  // Error state
  if (error) {
    return (
      <section id="games" className="bg-muted/30 py-16 md:py-24">
        <div className="mx-auto max-w-5xl px-6 text-center">
          <h2 className="text-3xl font-medium tracking-tight sm:text-4xl">Today's Games</h2>
          <p className="mt-4 text-destructive">{error}</p>
          <Button onClick={() => window.location.reload()} className="mt-4">
            Retry
          </Button>
        </div>
      </section>
    );
  }


  return (
    <section id="games" className="bg-muted/30 py-16 md:py-24">
      <div className="mx-auto max-w-5xl px-6">
        <div className="mb-12 text-center">
          <h2 className="text-3xl font-medium tracking-tight sm:text-4xl">Today's Games</h2>
          <p className="mt-4 text-muted-foreground">Player points props for upcoming matchups</p>
        </div>

        <AnimatedGroup variants={transitionVariants} className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {games.map((game) => (
            <motion.div
              key={game.id}
              className={cn(
                "relative flex flex-col justify-between w-full p-6 overflow-hidden rounded-xl shadow-sm transition-shadow duration-300 ease-in-out group hover:shadow-lg min-h-[180px]",
                "bg-card text-card-foreground border border-border/50",
              )}
              variants={cardAnimation}
              whileHover="hover"
            >
              {/* Rest of your JSX unchanged */}
              <motion.img
                src={teamLogos[game.homeTeam.abbr] || "/fallback-logo.svg"}
                alt={`${game.homeTeam.name} logo`}
                className="absolute -right-6 -bottom-6 w-36 h-36 object-contain opacity-10 group-hover:opacity-20 transition-opacity"
                variants={imageAnimation}
              />

              <div className="relative z-10 flex flex-col h-full">
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-3">
                  <Clock className="h-3 w-3" />
                  {game.time}
                </div>

                <h3 className="text-xl font-bold tracking-tight">
                  {game.awayTeam.abbr} @ {game.homeTeam.abbr}
                </h3>

                <Link
                  href={`/games/${game.id}`}
                  className="mt-auto pt-4 flex items-center text-sm font-semibold group-hover:underline"
                >
                  VIEW PLAYER POINTS
                  <motion.div variants={arrowAnimation}>
                    <ChevronRight className="ml-1 h-4 w-4" />
                  </motion.div>
                </Link>
              </div>
            </motion.div>
          ))}
        </AnimatedGroup>
      </div>
    </section>
  );
}

