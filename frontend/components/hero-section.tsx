"use client"
import React from "react"
import { AnimatedGroup } from "@/components/ui/animated-group"
import Link from "next/link"
import { InfiniteSlider } from "@/components/ui/infinite-slider"
import { ProgressiveBlur } from "@/components/ui/progressive-blur"
import { GradientButton } from "@/components/ui/gradient-button"
import { Bet365Logo, DraftKingsLogo, FanDuelLogo, BetMGMLogo} from "@/components/ui/logos1/index"
import { Timeline } from "@/components/ui/timeline"
import type { Variants } from "motion/react"

const transitionVariants: { item: Variants } = {
  item: {
    hidden: {
      opacity: 0,
      filter: "blur(12px)",
      y: 12,
    },
    visible: {
      opacity: 1,
      filter: "blur(0px)",
      y: 0,
      transition: {
        type: "spring",
        bounce: 0.3,
        duration: 1.5,
      },
    },
  },
}

export function HeroSection() {
  return (
    <main className="overflow-hidden pt-16">
        <section>
          <div className="relative mx-auto max-w-6xl px-6 pt-32 pb-16 lg:pb-24 lg:pt-48">
            <div className="relative z-10 mx-auto max-w-4xl text-center">
              <AnimatedGroup
                variants={{
                  container: {
                    visible: {
                      transition: {
                        staggerChildren: 0.05,
                        delayChildren: 0.75,
                      },
                    },
                  },
                  ...transitionVariants,
                }}
              >
                <h1 className="text-balance text-4xl font-medium sm:text-5xl md:text-6xl">sharpeye.io</h1>

                <p className="mx-auto mt-6 max-w-2xl text-pretty text-lg">
                  We surface data so you can make informed decisions
                </p>

                <div className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-6">
                  <GradientButton asChild>
                    <Link href="/todaysGames">View Today&apos;s Games</Link>
                  </GradientButton>
                </div>
              </AnimatedGroup>
            </div>
          </div>
        </section>
        <TimelineSection />
        <LogoCloud />
    </main>
  )
}

// Timeline section with SharpEye.ai data
const TimelineSection = () => {
  const timelineData = [
    {
      title: "Data Collection",
      content: (
        <div>
          <p className="text-neutral-800 dark:text-neutral-200 text-xs md:text-sm font-normal mb-4">
            We pull player statistics, team defense metrics, and odds from major sportsbooks into one place.
          </p>
          <div className="mb-4">
            <div className="flex gap-2 items-center text-neutral-700 dark:text-neutral-300 text-xs md:text-sm">
              ✓ Current and historical player statistics
            </div>
            <div className="flex gap-2 items-center text-neutral-700 dark:text-neutral-300 text-xs md:text-sm">
              ✓ Team defensive analytics by position
            </div>
            <div className="flex gap-2 items-center text-neutral-700 dark:text-neutral-300 text-xs md:text-sm">
              ✓ Live lines from major sportsbooks
            </div>
            <div className="flex gap-2 items-center text-neutral-700 dark:text-neutral-300 text-xs md:text-sm">
              ✓ Pace and matchup context
            </div>
          </div>
        </div>
      ),
    },
    {
      title: "Statistical Modeling",
      content: (
        <div>
          <p className="text-neutral-800 dark:text-neutral-200 text-xs md:text-sm font-normal mb-4">
            Our models run simulations to generate probability distributions for player scoring outcomes.
          </p>
          <div className="mb-4">
            <div className="flex gap-2 items-center text-neutral-700 dark:text-neutral-300 text-xs md:text-sm">
              ✓ 80+ Engineered Features fed to an XGBoost model including player form, matchup data, and pace of play
            </div>
            <div className="flex gap-2 items-center text-neutral-700 dark:text-neutral-300 text-xs md:text-sm">
              ✓ Monte Carlo simulation models the probability distribution around sportsbook prop lines
            </div>
            <div className="flex gap-2 items-center text-neutral-700 dark:text-neutral-300 text-xs md:text-sm">
              ✓ Rolling averages and situational splits for additional context
            </div>
          </div>
        </div>
      ),
    },
    {
      title: "Market Context",
      content: (
        <div>
          <p className="text-neutral-800 dark:text-neutral-200 text-xs md:text-sm font-normal mb-4">
            See how our modeled distributions compare to current sportsbook lines.
          </p>
          <div className="mb-4">
            <div className="flex gap-2 items-center text-neutral-700 dark:text-neutral-300 text-xs md:text-sm">
              ✓ Projected ranges vs. market lines
            </div>
            <div className="flex gap-2 items-center text-neutral-700 dark:text-neutral-300 text-xs md:text-sm">
              ✓ Probability distributions with confidence intervals
            </div>
            <div className="flex gap-2 items-center text-neutral-700 dark:text-neutral-300 text-xs md:text-sm">
              ✓ Data-driven scoring insights
            </div>
          </div>
        </div>
      ),
    },
  ]

  return <Timeline data={timelineData} />
}

const LogoCloud = () => {
  return (
    <section className="bg-background py-16 md:py-24 lg:py-32">
      {" "}
      {/* Evenly spaced padding */}
      <div className="group relative m-auto max-w-7xl px-8">
        {" "}
        {/* Wider container + padding */}
        <div className="flex flex-col items-center md:flex-row">
          <div className="inline md:max-w-52 md:border-r md:pr-8">
            {" "}
            {/* Wider text area */}
            <p className="text-center text-base md:text-lg">
              {" "}
              {/* Bigger text */}
              Contextualize player prop markets across major sportsbooks
            </p>
          </div>
          <div className="relative py-4 md:py-8 md:w-[calc(100%-13rem)] ">
            {" "}
       
            <InfiniteSlider speedOnHover={20} speed={40} gap={140}>
              {" "}
         
              <div className="flex items-center">
                <FanDuelLogo className="h-10 w-auto md:h-12" /> 
              </div>
              <div className="flex items-center">
                <DraftKingsLogo className="h-10 w-auto md:h-12" /> 
              </div>
              <div className="flex items-center">
                <Bet365Logo className="h-10 w-auto md:h-12" /> 
              </div>
              <div className="flex items-center">
                <BetMGMLogo className="h-10 w-auto md:h-12" /> 
              </div>
             
              <div className="flex items-center">
                <FanDuelLogo className="h-10 w-auto md:h-12" />
              </div>
              <div className="flex items-center">
                <DraftKingsLogo className="h-10 w-auto md:h-12" /> 
              </div>
              <div className="flex items-center">
                <Bet365Logo className="h-10 w-auto md:h-12" /> 
              </div>
              <div className="flex items-center">
                <BetMGMLogo className="h-10 w-auto md:h-12" /> 
              </div>
               
            </InfiniteSlider>
         
            <div className="bg-linear-to-r from-background absolute inset-y-0 left-0 w-24"></div>
            <div className="bg-linear-to-l from-background absolute inset-y-0 right-0 w-24"></div>
            <ProgressiveBlur
              className="pointer-events-none absolute left-0 top-0 h-full w-24"
              direction="left"
              blurIntensity={1}
            />
            <ProgressiveBlur
              className="pointer-events-none absolute right-0 top-0 h-full w-24"
              direction="right"
              blurIntensity={1}
            />
          </div>
        </div>
      </div>
    </section>
  )
}
