"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "motion/react"
import { Clock, ChevronDown, Loader2 } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { AnimatedGroup } from "@/components/ui/animated-group"
import { Collapsible, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Bet365Logo, DraftKingsLogo, FanDuelLogo, BetMGMLogo } from "@/components/ui/logos1/index"
import { PredictionResult, type PredictionResponse } from "@/components/prediction-result"

interface BookmakerOdds {
  bookmaker_key: string
  bookmaker_name: string
  over_odds: number | null
  under_odds: number | null
}

interface PlayerDTO {
  player_id: string
  name: string
  prop_line: number
  bookmakers: BookmakerOdds[]
  data_as_of: string
}

const bookmakerLogos: Record<string, React.ComponentType<{ className?: string }>> = {
  fanduel: FanDuelLogo,
  draftkings: DraftKingsLogo,
  bet365: Bet365Logo,
  betmgm: BetMGMLogo,
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
}


const transitionVariants = {
  container: {
    visible: {
      transition: {
        staggerChildren: 0.05,
        delayChildren: 0.1,
      },
    },
  },
  item: {
    hidden: {
      opacity: 0,
      y: 15,
      filter: "blur(4px)",
    },
    visible: {
      opacity: 1,
      y: 0,
      filter: "blur(0px)",
      transition: {
        type: "spring" as const,
        bounce: 0.3,
        duration: 0.6,
      },
    },
  },
}

const dropdownVariants = {
  hidden: {
    opacity: 0,
    height: 0,
    y: -8,
  },
  visible: {
    opacity: 1,
    height: "auto",
    y: 0,
    transition: {
      height: { duration: 0.3, ease: [0.4, 0, 0.2, 1] as const },
      opacity: { duration: 0.25, ease: "easeOut" as const, delay: 0.05 },
      y: { duration: 0.25, ease: "easeOut" as const, delay: 0.05 },
    },
  },
  exit: {
    opacity: 0,
    height: 0,
    y: -8,
    transition: {
      height: { duration: 0.25, ease: [0.4, 0, 0.2, 1] as const, delay: 0.05 },
      opacity: { duration: 0.2, ease: "easeIn" as const },
      y: { duration: 0.2, ease: "easeIn" as const },
    },
  },
}

const rowVariants = {
  hidden: { opacity: 0, x: -10 },
  visible: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: {
      delay: i * 0.05,
      duration: 0.25,
      ease: "easeOut" as const,
    },
  }),
}

interface PlayerPropCardProps {
  player: PlayerDTO
  homeTeam?: string
  awayTeam?: string
}

function PlayerPropCard({ player, homeTeam, awayTeam }: PlayerPropCardProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [customLine, setCustomLine] = useState(player.prop_line)
  const [customOverOdds, setCustomOverOdds] = useState(-110)
  const [customUnderOdds, setCustomUnderOdds] = useState(-110)

  // Prediction state
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null)
  const [predictionLoading, setPredictionLoading] = useState(false)
  const [predictionError, setPredictionError] = useState<string | null>(null)
  const [lastAnalyzedLine, setLastAnalyzedLine] = useState<number | null>(null)

  const minLine = Math.floor(player.prop_line - 10)
  const maxLine = Math.ceil(player.prop_line + 10)

  const gameDate = new Date().toISOString().split("T")[0]

  const handleAnalyze = async (propLine: number, overOdds: number, underOdds: number) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL
    if (!apiUrl) {
      setPredictionError("API URL is not configured")
      return
    }

    setPredictionLoading(true)
    setPredictionError(null)

    try {
      const response = await fetch(`${apiUrl}/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          player: player.name,
          home_team: homeTeam,
          away_team: awayTeam,
          game_date: gameDate,
          prop_line: propLine,
          over_odds: overOdds,
          under_odds: underOdds,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to get prediction: ${response.status}`)
      }

      const data: PredictionResponse = await response.json()
      setPrediction(data)
      setLastAnalyzedLine(propLine)
    } catch (err) {
      setPredictionError(err instanceof Error ? err.message : "Failed to get prediction")
      setPrediction(null)
    } finally {
      setPredictionLoading(false)
    }
  }

  return (
    <motion.div variants={transitionVariants.item}>
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <div className="rounded-xl border border-border bg-card shadow-sm transition-all duration-300 hover:shadow-md hover:border-border/80">
          <CollapsibleTrigger className="w-full">
            <div className="flex items-center justify-between p-4 cursor-pointer group">
              <div className="flex items-center gap-3">
                <div className="text-left">
                  <h3 className="text-lg font-semibold text-card-foreground">{player.name}</h3>
                  <p className="text-sm text-muted-foreground">
                    Points Props • Line: {player.prop_line}
                  </p>
                </div>
              </div>
              <motion.div animate={{ rotate: isOpen ? 180 : 0 }} transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}>
                <ChevronDown className="h-5 w-5 text-muted-foreground" />
              </motion.div>
            </div>
          </CollapsibleTrigger>
          <AnimatePresence initial={false}>
            {isOpen && (
              <motion.div
                variants={dropdownVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                className="overflow-hidden"
              >
                <div className="border-t border-border px-4 pb-5 pt-4">
                  <div className="hidden md:grid md:grid-cols-[minmax(100px,140px)_1fr_auto] gap-4 px-3 pb-3 text-xs text-muted-foreground uppercase tracking-wide font-medium border-b border-border/50 mb-3">
                    <span className="text-left">Sportsbook</span>
                    <span className="text-center">Over/Under</span>
                    <span className="text-right w-20">Action</span>
                  </div>

                  <div className="hidden md:block space-y-2">
                    {player.bookmakers.map((bookmaker, idx) => {
                      const LogoComponent = bookmakerLogos[bookmaker.bookmaker_key] || null
                      return (
                        <motion.div
                          key={bookmaker.bookmaker_key}
                          custom={idx}
                          variants={rowVariants}
                          initial="hidden"
                          animate="visible"
                          className="grid grid-cols-[minmax(100px,140px)_1fr_auto] gap-4 items-center py-3 px-3 rounded-lg bg-muted/40 hover:bg-muted/60 transition-colors duration-200"
                        >
                          <div className="flex items-center justify-start">
                            <div className="flex items-center justify-center w-[100px] h-[32px]">
                              {LogoComponent ? (
                                <LogoComponent className="h-6 w-auto max-w-[100px] object-contain" />
                              ) : (
                                <span className="text-sm font-medium">{bookmaker.bookmaker_name}</span>
                              )}
                            </div>
                          </div>
                          <div className="text-center">
                            <span
                              className={cn(
                                "font-medium text-sm",
                                bookmaker.over_odds !== null && bookmaker.under_odds !== null &&
                                  bookmaker.over_odds <= bookmaker.under_odds && "text-emerald-600 dark:text-emerald-400",
                              )}
                            >
                              {bookmaker.over_odds !== null ? (bookmaker.over_odds > 0 ? "+" : "") + bookmaker.over_odds : "N/A"}
                            </span>
                            <span className="text-muted-foreground mx-1">/</span>
                            <span
                              className={cn(
                                "font-medium text-sm",
                                bookmaker.over_odds !== null && bookmaker.under_odds !== null &&
                                  bookmaker.under_odds < bookmaker.over_odds && "text-red-600 dark:text-red-400",
                              )}
                            >
                              {bookmaker.under_odds !== null ? (bookmaker.under_odds > 0 ? "+" : "") + bookmaker.under_odds : "N/A"}
                            </span>
                          </div>
                          <div className="flex justify-end w-20">
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-8 px-3 text-xs font-medium hover:bg-primary hover:text-primary-foreground transition-colors duration-200 bg-transparent"
                              disabled={predictionLoading}
                              onClick={() => handleAnalyze(
                                player.prop_line,
                                bookmaker.over_odds ?? -110,
                                bookmaker.under_odds ?? -110
                              )}
                            >
                              {predictionLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : "Analyze"}
                            </Button>
                          </div>
                        </motion.div>
                      )
                    })}
                  </div>

                  <div className="md:hidden space-y-3">
                    {player.bookmakers.map((bookmaker, idx) => {
                      const LogoComponent = bookmakerLogos[bookmaker.bookmaker_key] || null
                      return (
                        <motion.div
                          key={bookmaker.bookmaker_key}
                          custom={idx}
                          variants={rowVariants}
                          initial="hidden"
                          animate="visible"
                          className="flex flex-col items-center p-4 rounded-lg bg-muted/40 hover:bg-muted/60 transition-colors duration-200 gap-3"
                        >
                          <div className="flex items-center justify-center w-[100px] h-[32px]">
                            {LogoComponent ? (
                              <LogoComponent className="h-6 w-auto max-w-[100px] object-contain" />
                            ) : (
                              <span className="text-sm font-medium">{bookmaker.bookmaker_name}</span>
                            )}
                          </div>
                          <div className="flex items-center justify-center gap-6 w-full">
                            <div className="flex flex-col items-center">
                              <span className="text-[10px] uppercase text-muted-foreground tracking-wide mb-1">
                                Over/Under
                              </span>
                              <div>
                                <span
                                  className={cn(
                                    "font-medium text-sm",
                                    bookmaker.over_odds !== null && bookmaker.under_odds !== null &&
                                      bookmaker.over_odds <= bookmaker.under_odds &&
                                      "text-emerald-600 dark:text-emerald-400",
                                  )}
                                >
                                  {bookmaker.over_odds !== null ? (bookmaker.over_odds > 0 ? "+" : "") + bookmaker.over_odds : "N/A"}
                                </span>
                                <span className="text-muted-foreground mx-1">/</span>
                                <span
                                  className={cn(
                                    "font-medium text-sm",
                                    bookmaker.over_odds !== null && bookmaker.under_odds !== null &&
                                      bookmaker.under_odds < bookmaker.over_odds && "text-red-600 dark:text-red-400",
                                  )}
                                >
                                  {bookmaker.under_odds !== null ? (bookmaker.under_odds > 0 ? "+" : "") + bookmaker.under_odds : "N/A"}
                                </span>
                              </div>
                            </div>
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            className="w-full h-10 text-sm font-medium hover:bg-primary hover:text-primary-foreground transition-colors duration-200 bg-transparent"
                            disabled={predictionLoading}
                            onClick={() => handleAnalyze(
                              player.prop_line,
                              bookmaker.over_odds ?? -110,
                              bookmaker.under_odds ?? -110
                            )}
                          >
                            {predictionLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Analyze"}
                          </Button>
                        </motion.div>
                      )
                    })}
                  </div>

                  <div className="mt-5 pt-4 border-t border-border/50">
                    <h4 className="text-sm font-semibold text-card-foreground mb-4">Custom Analysis</h4>
                    <div className="space-y-5">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <label className="text-sm text-muted-foreground">Points Line</label>
                          <span className="text-sm font-bold text-card-foreground bg-muted px-2 py-0.5 rounded">
                            {customLine.toFixed(1)}
                          </span>
                        </div>
                        <Slider
                          value={[customLine]}
                          onValueChange={(value) => setCustomLine(value[0])}
                          min={minLine}
                          max={maxLine}
                          step={0.5}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>{minLine}</span>
                          <span>{maxLine}</span>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <label className="text-sm text-muted-foreground">Over Odds</label>
                          <span className="text-sm font-bold text-card-foreground bg-muted px-2 py-0.5 rounded">
                            {customOverOdds > 0 ? "+" : ""}
                            {customOverOdds}
                          </span>
                        </div>
                        <Slider
                          value={[customOverOdds]}
                          onValueChange={(value) => setCustomOverOdds(value[0])}
                          min={-300}
                          max={200}
                          step={5}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>-300</span>
                          <span>+200</span>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <label className="text-sm text-muted-foreground">Under Odds</label>
                          <span className="text-sm font-bold text-card-foreground bg-muted px-2 py-0.5 rounded">
                            {customUnderOdds > 0 ? "+" : ""}
                            {customUnderOdds}
                          </span>
                        </div>
                        <Slider
                          value={[customUnderOdds]}
                          onValueChange={(value) => setCustomUnderOdds(value[0])}
                          min={-200}
                          max={200}
                          step={5}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>-200</span>
                          <span>+200</span>
                        </div>
                      </div>
                      <Button
                        className="w-full mt-2 font-medium"
                        size="default"
                        disabled={predictionLoading}
                        onClick={() => handleAnalyze(customLine, customOverOdds, customUnderOdds)}
                      >
                        {predictionLoading ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            Analyzing...
                          </>
                        ) : (
                          "Analyze Custom Line"
                        )}
                      </Button>
                    </div>
                  </div>

                  {/* Prediction Error */}
                  {predictionError && (
                    <div className="mt-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                      <p className="text-sm text-destructive">{predictionError}</p>
                    </div>
                  )}

                  {/* Prediction Result */}
                  <AnimatePresence>
                    {prediction && lastAnalyzedLine !== null && (
                      <PredictionResult
                        prediction={prediction}
                        propLine={lastAnalyzedLine}
                        onClose={() => {
                          setPrediction(null)
                          setLastAnalyzedLine(null)
                        }}
                      />
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </Collapsible>
    </motion.div>
  )
}

interface PlayerPropsViewProps {
  gameId: string
  homeTeam?: string
  awayTeam?: string
  gameTime?: string
}



export function PlayerPropsView({ gameId, homeTeam, awayTeam, gameTime }: PlayerPropsViewProps) {
  const [players, setPlayers] = useState<PlayerDTO[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000)

      try {
        setLoading(true)
        setError(null)

        const apiUrl = process.env.NEXT_PUBLIC_API_URL
        if (!apiUrl) {
          throw new Error("API URL is not configured")
        }

        const playersResponse = await fetch(`${apiUrl}/nba/games/${gameId}/players`, { signal: controller.signal })
        clearTimeout(timeoutId)

        if (!playersResponse.ok) {
          if (playersResponse.status === 404) {
            throw new Error("No player odds available for this game. Check back at 4 PM ET.")
          }
          throw new Error(`Failed to fetch players: ${playersResponse.status}`)
        }

        const data: PlayerDTO[] = await playersResponse.json()
        setPlayers(data)
      } catch (err) {
        if (err instanceof Error && err.name === "AbortError") {
          setError("Request timed out. Please try again.")
        } else {
          setError(err instanceof Error ? err.message : "Failed to load player props")
        }
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [gameId, homeTeam, awayTeam])

  const renderHeader = (subtitle?: string) => (
    <div className="mb-10 text-center">
      <div className="flex items-center justify-center gap-4 mb-2">
        {awayTeam && teamLogos[awayTeam] && (
          <img
            src={teamLogos[awayTeam]}
            alt={awayTeam}
            className="w-12 h-12 object-contain"
          />
        )}
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
          {awayTeam && homeTeam ? `${awayTeam} @ ${homeTeam}` : "Player Props"}
        </h1>
        {homeTeam && teamLogos[homeTeam] && (
          <img
            src={teamLogos[homeTeam]}
            alt={homeTeam}
            className="w-12 h-12 object-contain"
          />
        )}
      </div>
      {gameTime && (
        <div className="flex items-center justify-center gap-1.5 text-sm text-muted-foreground">
          <Clock className="h-4 w-4" />
          {gameTime}
        </div>
      )}
      {subtitle && <p className="mt-2 text-muted-foreground">{subtitle}</p>}
    </div>
  )

  if (loading) {
    return (
      <section className="py-16 md:py-24">
        <div className="mx-auto max-w-5xl px-6">
          {renderHeader("Loading player props...")}
          <div className="grid grid-cols-1 gap-4">
            {Array(6)
              .fill(0)
              .map((_, i) => (
                <div key={i} className="animate-pulse bg-muted rounded-xl h-[80px]" />
              ))}
          </div>
        </div>
      </section>
    )
  }

  if (error) {
    return (
      <section className="py-16 md:py-24">
        <div className="mx-auto max-w-5xl px-6 text-center">
          {renderHeader()}
          <p className="mt-4 text-destructive">{error}</p>
          <Button onClick={() => window.location.reload()} className="mt-4">
            Retry
          </Button>
        </div>
      </section>
    )
  }

  if (players.length === 0) {
    return (
      <section className="py-16 md:py-24">
        <div className="mx-auto max-w-5xl px-6 text-center">
          {renderHeader("No player props available for this game yet.")}
        </div>
      </section>
    )
  }

  return (
    <section className="pb-16 md:pb-24">
      <div className="mx-auto max-w-5xl px-6">
        {renderHeader("Player Points Props")}
        <AnimatedGroup variants={transitionVariants} className="grid grid-cols-1 gap-4">
          {players.map((player) => (
            <PlayerPropCard
              key={player.player_id}
              player={player}
              homeTeam={homeTeam}
              awayTeam={awayTeam}
            />
          ))}
        </AnimatedGroup>
      </div>
    </section>
  )
}
