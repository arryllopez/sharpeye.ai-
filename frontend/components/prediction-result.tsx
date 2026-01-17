"use client"

import { motion } from "motion/react"
import { X, TrendingUp, TrendingDown, Minus, Activity, Target, Zap, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useMemo } from "react"
import { AreaChart, Area, XAxis, YAxis, ReferenceLine, ResponsiveContainer, Tooltip } from "recharts"

interface PlayerStats {
  last_5_avg: number
  last_10_avg: number
  consistency_std: number
  minutes_per_game: number
  rest_days: number
}

interface MatchupAnalysis {
  opponent_defense_ppg: number
  defense_vs_position: number
  defense_quality: "Weak" | "Average" | "Strong"
}

interface PaceContext {
  player_team_pace: number
  opponent_pace: number
  expected_game_pace: number
  pace_environment: "Fast" | "Average" | "Slow"
  expected_possessions: number
}

interface MonteCarloAnalysis {
  probability_over: number
  probability_under: number
  edge: number
  confidence_score: number
  percentiles: Record<number, number>
  recommendation: "OVER" | "UNDER" | "PASS"
}

interface PredictionInterval {
  lower_90: number
  upper_90: number
  model_mae: number
}

interface KeyFactors {
  recent_form: string
  matchup_favorability: "Favorable" | "Neutral" | "Unfavorable"
  pace_impact: "Positive" | "Neutral" | "Negative"
  rest_impact: "Well-rested" | "Normal" | "Back-to-back"
}

export interface PredictionResponse {
  player_name: string
  position: string
  team: string
  opponent: string
  location: "HOME" | "AWAY"
  game_date: string
  predicted_points: number
  player_stats: PlayerStats
  matchup_analysis: MatchupAnalysis
  pace_context: PaceContext
  prediction_interval: PredictionInterval
  monte_carlo: MonteCarloAnalysis | null
  key_factors: KeyFactors
}

interface PredictionResultProps {
  prediction: PredictionResponse
  propLine: number
  onClose: () => void
}

// Generate normal distribution curve data from percentiles
function generateDistributionData(
  predicted: number,
  percentiles: Record<number, number>,
  propLine: number
) {
  const p5 = percentiles[5] ?? predicted - 10
  const p95 = percentiles[95] ?? predicted + 10
  const std = (p95 - p5) / 3.29

  const points: { x: number; y: number; isUnder: boolean }[] = []
  const min = Math.max(0, predicted - 4 * std)
  const max = predicted + 4 * std
  const step = (max - min) / 60

  for (let x = min; x <= max; x += step) {
    const y = Math.exp(-0.5 * Math.pow((x - predicted) / std, 2)) / (std * Math.sqrt(2 * Math.PI))
    points.push({ x: Math.round(x * 10) / 10, y, isUnder: x <= propLine })
  }

  return points
}

export function PredictionResult({ prediction, propLine, onClose }: PredictionResultProps) {
  const diff = prediction.predicted_points - propLine
  const isOver = diff > 0

  // Generate distribution data for chart
  const distributionData = useMemo(() => {
    if (!prediction.monte_carlo) return []
    return generateDistributionData(
      prediction.predicted_points,
      prediction.monte_carlo.percentiles,
      propLine
    )
  }, [prediction.predicted_points, prediction.monte_carlo, propLine])

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="mt-4 rounded-lg border border-border bg-background p-4 space-y-4"
    >
      <div className="flex items-center justify-between">
        <h4 className="font-semibold text-card-foreground">Sharpeye's analysis: {prediction.player_name}</h4>
        <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Main Prediction */}
      <div className="text-center py-4 rounded-lg bg-muted/50">
        <p className="text-sm text-muted-foreground mb-1">Predicted Points Scored</p>
        <p className="text-4xl font-bold text-card-foreground">{prediction.predicted_points.toFixed(1)}</p>
        <div className="flex items-center justify-center gap-2 mt-2">
          <span className="text-sm text-muted-foreground">Line: {propLine}</span>
          <span className={cn(
            "text-sm font-medium flex items-center gap-1",
            isOver ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"
          )}>
            {isOver ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
            {isOver ? "+" : ""}{diff.toFixed(1)}
          </span>
        </div>
      </div>

      {/* Monte Carlo Results (if available) */}
      {prediction.monte_carlo && (
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
            <p className="text-xs text-muted-foreground mb-1">Over Probability</p>
            <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400">
              {(prediction.monte_carlo.probability_over * 100).toFixed(1)}%
            </p>
          </div>
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
            <p className="text-xs text-muted-foreground mb-1">Under Probability</p>
            <p className="text-xl font-bold text-red-600 dark:text-red-400">
              {(prediction.monte_carlo.probability_under * 100).toFixed(1)}%
            </p>
          </div>
          <div className="p-3 rounded-lg bg-muted/50">
            <p className="text-xs text-muted-foreground mb-1">Predicted Edge</p>
            <p className={cn(
              "text-xl font-bold",
              prediction.monte_carlo.edge > 0 ? "text-emerald-600 dark:text-emerald-400" : "text-muted-foreground"
            )}>
              {prediction.monte_carlo.edge > 0 ? "+" : ""}{prediction.monte_carlo.edge.toFixed(1)}%
            </p>
            <p className="text-[10px] text-muted-foreground mt-1">Based on model prediction</p>
          </div>
          <div className="p-3 rounded-lg bg-muted/50">
            <p className="text-xs text-muted-foreground mb-1">Model Confidence</p>
            <p className="text-xl font-bold text-card-foreground">
              {prediction.monte_carlo.confidence_score.toFixed(0)}%
            </p>
          </div>
        </div>
      )}

      {/* Recommendation Badge */}
      {prediction.monte_carlo && (
        <div className="flex justify-center">
          <span className={cn(
            "px-4 py-2 rounded-full text-sm font-semibold",
            prediction.monte_carlo.recommendation === "OVER" && "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400",
            prediction.monte_carlo.recommendation === "UNDER" && "bg-red-500/20 text-red-600 dark:text-red-400",
            prediction.monte_carlo.recommendation === "PASS" && "bg-muted text-muted-foreground"
          )}>
            Recommendation: {prediction.monte_carlo.recommendation}
          </span>
        </div>
      )}

      {prediction.monte_carlo && distributionData.length > 0 && (
        <div className="space-y-2">
          <h5 className="text-sm font-medium text-card-foreground">Outcome Distribution</h5>
          <div className="h-32 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={distributionData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                <defs>
                  <linearGradient id="underGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.05} />
                  </linearGradient>
                  <linearGradient id="overGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="x"
                  type="number"
                  domain={['dataMin', 'dataMax']}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 10, fill: '#888' }}
                  tickFormatter={(v) => Math.round(v).toString()}
                  ticks={[
                    Math.round(distributionData[0]?.x ?? 0),
                    Math.round(propLine),
                    Math.round(prediction.predicted_points),
                    Math.round(distributionData[distributionData.length - 1]?.x ?? 40)
                  ].filter((v, i, a) => a.indexOf(v) === i).sort((a, b) => a - b)}
                />
                <YAxis hide domain={[0, 'auto']} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-background border border-border rounded px-2 py-1 text-xs">
                          {payload[0].payload.x.toFixed(1)} pts
                        </div>
                      )
                    }
                    return null
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="y"
                  stroke="#10b981"
                  fill="url(#overGradient)"
                  strokeWidth={2}
                />
                <ReferenceLine
                  x={propLine}
                  stroke="#f59e0b"
                  strokeWidth={2}
                  strokeDasharray="4 4"
                  label={{
                    value: `Line: ${propLine}`,
                    position: 'top',
                    fill: '#f59e0b',
                    fontSize: 10,
                  }}
                />
                <ReferenceLine
                  x={prediction.predicted_points}
                  stroke="#3b82f6"
                  strokeWidth={2}
                  label={{
                    value: `Pred: ${prediction.predicted_points.toFixed(1)}`,
                    position: 'top',
                    fill: '#3b82f6',
                    fontSize: 10,
                  }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center gap-4 text-[10px] text-muted-foreground">
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-amber-500 inline-block" style={{ borderStyle: 'dashed' }}></span>
              Prop Line
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-blue-500 inline-block"></span>
              Prediction
            </span>
          </div>
          <p className="text-[10px] text-muted-foreground text-center">
            Based on 10,000 simulations
          </p>
        </div>
      )}

 
      <div className="space-y-2">
        <h5 className="text-sm font-medium text-card-foreground flex items-center gap-2">
          <Activity className="h-4 w-4" /> Recent Performance
        </h5>
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="p-2 rounded bg-muted/30">
            <p className="text-xs text-muted-foreground">L5 Avg</p>
            <p className="font-semibold">{prediction.player_stats.last_5_avg.toFixed(1)}</p>
          </div>
          <div className="p-2 rounded bg-muted/30">
            <p className="text-xs text-muted-foreground">L10 Avg</p>
            <p className="font-semibold">{prediction.player_stats.last_10_avg.toFixed(1)}</p>
          </div>
          <div className="p-2 rounded bg-muted/30">
            <p className="text-xs text-muted-foreground">L5 Minutes/Game</p>
            <p className="font-semibold">{prediction.player_stats.minutes_per_game.toFixed(1)}</p>
          </div>
        </div>
      </div>


      <div className="space-y-3">
        <h5 className="text-sm font-medium text-card-foreground flex items-center gap-2">
          Key Factors
        </h5>
        <div className="space-y-3 text-sm">
         
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 p-2 rounded bg-muted/20">
            <span className="text-muted-foreground font-medium">Matchup</span>
            <span className={cn(
              "font-medium text-right",
              prediction.key_factors.matchup_favorability === "Favorable" && "text-emerald-600 dark:text-emerald-400",
              prediction.key_factors.matchup_favorability === "Unfavorable" && "text-red-600 dark:text-red-400"
            )}>
              {prediction.key_factors.matchup_favorability}
              <span className="block sm:inline sm:ml-1 text-xs text-muted-foreground font-normal">
                ({prediction.matchup_analysis.opponent_defense_ppg.toFixed(1)} OPP PPG allowed L5)
              </span>
            </span>
          </div>


          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 p-2 rounded bg-muted/20">
            <span className="text-muted-foreground font-medium">Rest</span>
            <span className={cn(
              "font-medium text-right",
              prediction.key_factors.rest_impact === "Well-rested" && "text-emerald-600 dark:text-emerald-400",
              prediction.key_factors.rest_impact === "Back-to-back" && "text-red-600 dark:text-red-400"
            )}>
              {prediction.key_factors.rest_impact}
              <span className="block sm:inline sm:ml-1 text-xs text-muted-foreground font-normal">
                ({prediction.player_stats.rest_days} {prediction.player_stats.rest_days === 1 ? "day" : "days"} since last game)
              </span>
            </span>
          </div>

          <div className="flex flex-col gap-1 p-2 rounded bg-muted/20">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground font-medium">Expected Game Pace</span>
              <span className="font-medium text-right">
                {prediction.pace_context.expected_game_pace.toFixed(1)} poss/48 min
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              ({prediction.pace_context.player_team_pace.toFixed(1)} + {prediction.pace_context.opponent_pace.toFixed(1)}) / 2 from both teams L5
            </p>
          </div>
        </div>
      </div>


      <div className="text-center text-xs text-muted-foreground pt-2 border-t border-border/50">
        90% Confidence: {prediction.prediction_interval.lower_90.toFixed(1)} - {prediction.prediction_interval.upper_90.toFixed(1)} pts
        <span className="mx-2">•</span>
        Model MAE: ±{prediction.prediction_interval.model_mae.toFixed(1)} pts
      </div>
    </motion.div>
  )
}
