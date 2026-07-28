import { motion, useScroll, useTransform } from "framer-motion";
import { Tv, UtensilsCrossed, Music, Sparkles } from "lucide-react";
import { useRef } from "react";
import { Button } from "@/components/ui";

interface InteractiveHeroProps {
  userName: string;
}

export function InteractiveHero({ userName }: InteractiveHeroProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end start"],
  });

  const y1 = useTransform(scrollYProgress, [0, 1], [0, 200]);
  const y2 = useTransform(scrollYProgress, [0, 1], [0, -100]);
  const opacity = useTransform(scrollYProgress, [0, 0.8], [1, 0]);

  const firstName = userName.split(" ")[0];

  return (
    <div
      ref={containerRef}
      className="relative w-full h-[50vh] min-h-[400px] flex items-center justify-center overflow-hidden rounded-3xl bg-gradient-to-br from-background via-muted/30 to-background border border-border/50 shadow-sm mb-8"
    >
      {/* Background Orbs */}
      <motion.div
        style={{ y: y1 }}
        className="absolute top-10 left-10 w-64 h-64 bg-violet-500/20 rounded-full blur-3xl pointer-events-none"
      />
      <motion.div
        style={{ y: y2 }}
        className="absolute bottom-10 right-10 w-80 h-80 bg-emerald-500/20 rounded-full blur-3xl pointer-events-none"
      />
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-primary/10 rounded-full blur-3xl pointer-events-none"
      />

      {/* Content */}
      <motion.div
        style={{ opacity }}
        className="relative z-10 text-center px-4 max-w-3xl"
      >
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex justify-center mb-4"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium border border-primary/20">
            <Sparkles className="w-4 h-4" />
            <span>AI-Powered Recommendations</span>
          </div>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6"
        >
          Discover your next obsession,{" "}
          <span className="bg-gradient-to-r from-primary via-purple-400 to-primary bg-clip-text text-transparent bg-[length:200%_auto] animate-gradient">
            {firstName}
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="text-lg md:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto"
        >
          Explore personalized anime, uncover hidden culinary gems, and dive into fresh music tracks curated just for your taste.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="flex flex-wrap justify-center gap-4"
        >
          <Button
            size="lg"
            className="rounded-full shadow-lg hover:shadow-primary/25 transition-all group"
          >
            <Tv className="w-5 h-5 mr-2 group-hover:scale-110 transition-transform" />
            Anime
          </Button>
          <Button
            size="lg"
            variant="outline"
            className="rounded-full shadow-md hover:shadow-lg transition-all group bg-background/50 backdrop-blur-sm"
          >
            <UtensilsCrossed className="w-5 h-5 mr-2 group-hover:scale-110 transition-transform" />
            Food
          </Button>
          <Button
            size="lg"
            variant="outline"
            className="rounded-full shadow-sm hover:shadow-md transition-all group bg-background/50 backdrop-blur-sm"
          >
            <Music className="w-5 h-5 mr-2 group-hover:scale-110 transition-transform" />
            Music
          </Button>
        </motion.div>
      </motion.div>
    </div>
  );
}
