"use client"
import React from "react"
import { Menu, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { AnimatedGroup } from "@/components/ui/animated-group"
import { cn } from "@/lib/utils"
import Link from "next/link"
import { InfiniteSlider } from "@/components/ui/infinite-slider"
import { ProgressiveBlur } from "@/components/ui/progressive-blur"
import { GradientButton } from "@/components/ui/gradient-button"
import { Bet365Logo, DraftKingsLogo, FanDuelLogo, BetMGMLogo } from "@/components/ui/logos1/index"
import { Timeline } from "@/components/ui/timeline"
import { PopoverTrigger, PopoverTriggerButton, Popover } from "@/components/ui/popover-aria"

const transitionVariants = {
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
    <>
      <HeroHeader />

      <main className="overflow-hidden">
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
                    <Link href="#games">View Today&apos;s Games</Link>
                  </GradientButton>
                </div>
              </AnimatedGroup>
            </div>
          </div>
        </section>
        <TimelineSection />
        <LogoCloud />
      </main>
    </>
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
              ✓ Historical hit rates for similar situations
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

const menuItems = [{ name: "Today's Games", href: "#games" }]

const HeroHeader = () => {
  const [menuState, setMenuState] = React.useState(false)
  const [isScrolled, setIsScrolled] = React.useState(false)

  React.useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50)
    }
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  return (
    <header>
      <nav data-state={menuState && "active"} className="fixed group z-20 w-full px-2">
        <div
          className={cn(
            "mx-auto mt-2 max-w-6xl px-6 transition-all duration-300 lg:px-12",
            isScrolled && "bg-background/50 max-w-4xl rounded-2xl border backdrop-blur-lg lg:px-5",
          )}
        >
          <div className="relative flex flex-wrap items-center justify-between gap-6 py-3 lg:gap-0 lg:py-4">
            <div className="flex w-full justify-between lg:w-auto">
              <button
                onClick={() => setMenuState(!menuState)}
                aria-label={menuState == true ? "Close Menu" : "Open Menu"}
                className="relative z-20 -m-2.5 -mr-4 block cursor-pointer p-2.5 lg:hidden"
              >
                <Menu className="group-data-[state=active]:rotate-180 group-data-[state=active]:scale-0 group-data-[state=active]:opacity-0 m-auto size-6 duration-200" />
                <X className="group-data-[state=active]:rotate-0 group-data-[state=active]:scale-100 group-data-[state=active]:opacity-100 absolute inset-0 m-auto size-6 -rotate-180 scale-0 opacity-0 duration-200" />
              </button>
            </div>

            <div className="absolute inset-0 m-auto hidden size-fit lg:block">
              <ul className="flex gap-8 text-sm">
                {menuItems.map((item, index) => (
                  <li key={index}>
                    <Link
                      href={item.href}
                      className="text-muted-foreground hover:text-accent-foreground block duration-150"
                    >
                      <span>{item.name}</span>
                    </Link>
                  </li>
                ))}
                <li>
                  <PopoverTrigger>
                    <PopoverTriggerButton className="text-muted-foreground hover:text-accent-foreground block duration-150 cursor-pointer">
                      <span>Disclaimers</span>
                    </PopoverTriggerButton>
                    <Popover placement="bottom" className="max-w-xs">
                      <p className="text-sm text-muted-foreground">
                        sharpeye.io is a portfolio project demonstrating machine learning techniques. All projections are probabilistic estimates and may be incorrect. Use at your own risk. Bet responsibly.
                      </p>
                    </Popover>
                  </PopoverTrigger>
                </li>
              </ul>
            </div>

            <div className="bg-background group-data-[state=active]:block lg:group-data-[state=active]:flex mb-6 hidden w-full flex-wrap items-center justify-end space-y-8 rounded-3xl border p-6 shadow-2xl shadow-zinc-300/20 md:flex-nowrap lg:m-0 lg:flex lg:w-fit lg:gap-6 lg:space-y-0 lg:border-transparent lg:bg-transparent lg:p-0 lg:shadow-none dark:shadow-none dark:lg:bg-transparent">
              <div className="lg:hidden">
                <ul className="space-y-6 text-base">
                  {menuItems.map((item, index) => (
                    <li key={index}>
                      <Link
                        href={item.href}
                        className="text-muted-foreground hover:text-accent-foreground block duration-150"
                      >
                        <span>{item.name}</span>
                      </Link>
                    </li>
                  ))}
                  <li>
                    <PopoverTrigger>
                      <PopoverTriggerButton className="text-muted-foreground hover:text-accent-foreground block duration-150 cursor-pointer">
                        <span>Disclaimers</span>
                      </PopoverTriggerButton>
                      <Popover placement="bottom" className="max-w-xs">
                        <p className="text-sm text-muted-foreground">
                          sharpeye.io is a portfolio project demonstrating machine learning techniques. All projections are probabilistic estimates and may be incorrect. Use at your own risk. Bet responsibly.
                        </p>
                      </Popover>
                    </PopoverTrigger>
                  </li>
                </ul>
              </div>
              <div className="flex w-full flex-col space-y-3 sm:flex-row sm:gap-3 sm:space-y-0 md:w-fit">
                <Button asChild size="sm" className="bg-black text-white hover:bg-black/90">
                  <Link href="https://lawrence-lopez.vercel.app/" target="blank">
                    <span>Creator</span>
                  </Link>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </nav>
    </header>
  )
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
            {/* Taller + wider slider area */}
            <InfiniteSlider speedOnHover={20} speed={40} gap={140}>
              {" "}
              {/* Bigger gap */}
              <div className="flex items-center">
                <FanDuelLogo className="h-10 w-auto md:h-12" /> {/* 67% → 100% bigger */}
              </div>
              <div className="flex items-center">
                <DraftKingsLogo className="h-10 w-auto md:h-12" /> {/* 67% → 100% bigger */}
              </div>
              <div className="flex items-center">
                <Bet365Logo className="h-10 w-auto md:h-12" /> {/* 67% → 100% bigger */}
              </div>
              <div className="flex items-center">
                <BetMGMLogo className="h-10 w-auto md:h-12" /> {/* 67% → 100% bigger */}
              </div>
              <div className="flex items-center">
                <FanDuelLogo className="h-10 w-auto md:h-12" />
              </div>
              <div className="flex items-center">
                <DraftKingsLogo className="h-10 w-auto md:h-12" /> {/* 67% → 100% bigger */}
              </div>
              <div className="flex items-center">
                <Bet365Logo className="h-10 w-auto md:h-12" /> {/* 67% → 100% bigger */}
              </div>
              <div className="flex items-center">
                <BetMGMLogo className="h-10 w-auto md:h-12" /> {/* 67% → 100% bigger */}
              </div>
            </InfiniteSlider>
            {/* Wider fade/blur areas */}
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
