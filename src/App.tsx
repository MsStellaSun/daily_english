/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { 
  BookOpen, 
  History, 
  Home, 
  Info, 
  Loader2, 
  Sparkles, 
  Calendar,
  ChevronRight,
  TrendingUp
} from "lucide-react";
import { format } from "date-fns";
import { generateDailyPhrases } from "./services/geminiService";
import { Phrase, AppState, DailyData } from "./types";
import { loadState, saveState, getTodayData } from "./lib/storage";
import { PhraseCard } from "./components/PhraseCard";

type View = "home" | "history" | "about";

export default function App() {
  const [state, setState] = useState<AppState>(loadState());
  const [view, setView] = useState<View>("home");
  const [loading, setLoading] = useState(false);
  const [todayPhrases, setTodayPhrases] = useState<Phrase[]>([]);

  useEffect(() => {
    const initToday = async () => {
      const todaySlug = format(new Date(), "yyyy-MM-dd");
      const today = getTodayData(state.history);

      if (today) {
        setTodayPhrases(today.phrases);
      } else {
        setLoading(true);
        try {
          const fetched = await generateDailyPhrases();
          const newData: DailyData = { date: todaySlug, phrases: fetched };
          const newState = { ...state, history: [newData, ...state.history] };
          setState(newState);
          saveState(newState);
          setTodayPhrases(fetched);
        } catch (error) {
          console.error("Failed to fetch today's phrases", error);
        } finally {
          setLoading(false);
        }
      }
    };

    initToday();
  }, []);

  const toggleLearned = (phraseText: string) => {
    const alreadyLearned = state.learnedPhrases.includes(phraseText);
    const newLearned = alreadyLearned
      ? state.learnedPhrases.filter((p) => p !== phraseText)
      : [...state.learnedPhrases, phraseText];
    
    const newState = { ...state, learnedPhrases: newLearned };
    setState(newState);
    saveState(newState);
  };

  const calculateStreak = () => {
    if (state.history.length === 0) return 0;
    let streak = 0;
    const sortedHistory = [...state.history].sort((a, b) => b.date.localeCompare(a.date));
    
    // Check if the most recent entry is today or yesterday
    const today = format(new Date(), "yyyy-MM-dd");
    const lastDate = sortedHistory[0].date;
    
    // If last activity is too old, streak is 0
    // Simplified: just count consecutive days in history
    streak = sortedHistory.length; // This is a placeholder for a more complex date logic
    return streak;
  };

  const markAllLearned = () => {
    const allTodayPhrases = todayPhrases.map(p => p.phrase);
    const uniqueLearned = Array.from(new Set([...state.learnedPhrases, ...allTodayPhrases]));
    const newState = { ...state, learnedPhrases: uniqueLearned };
    setState(newState);
    saveState(newState);
  };

  const learnedCount = todayPhrases.filter(p => state.learnedPhrases.includes(p.phrase)).length;
  const progress = todayPhrases.length > 0 ? (learnedCount / todayPhrases.length) * 100 : 0;
  const streak = calculateStreak();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans selection:bg-brand-blue/10">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-6 sm:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-dark text-white font-bold text-sm tracking-tight">
              DE
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-slate-900 leading-none">Daily English</h1>
              <div className="flex items-center gap-1.5 mt-0.5">
                 <span className="w-1.5 h-1.5 rounded-full bg-brand-green animate-pulse"></span>
                 <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Pro Version</p>
              </div>
            </div>
          </div>
          
          <nav className="flex items-center gap-1">
            <button 
              onClick={() => setView("home")}
              className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-bold transition-all ${view === "home" ? "bg-slate-100 text-brand-dark" : "text-slate-500 hover:bg-slate-50"}`}
            >
              <Home className="h-3.5 w-3.5" />
              <span>Today</span>
            </button>
            <button 
              onClick={() => setView("history")}
              className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-bold transition-all ${view === "history" ? "bg-slate-100 text-brand-dark" : "text-slate-500 hover:bg-slate-50"}`}
            >
              <History className="h-3.5 w-3.5" />
              <span>Archive</span>
            </button>
            <button 
              onClick={() => setView("about")}
              className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-bold transition-all ${view === "about" ? "bg-slate-100 text-brand-dark" : "text-slate-500 hover:bg-slate-50"}`}
            >
              <BookOpen className="h-3.5 w-3.5" />
              <span>About Us</span>
            </button>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-8 sm:px-8">
        <AnimatePresence mode="wait">
          {view === "home" && (
            <motion.div
              key="home"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-6"
            >
              {/* Compact Daily Header */}
              <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
                <div>
                  <div className="inline-flex items-center gap-2 rounded-full bg-brand-dark/5 px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">
                    <Sparkles className="h-3 w-3 text-brand-yellow" /> Daily Challenge
                  </div>
                  <h2 className="text-3xl font-bold tracking-tight text-slate-900">
                    Master 5 phrases.
                  </h2>
                </div>
                
                <div className="flex items-center gap-4 bg-white border border-slate-200 rounded-2xl p-4 shadow-sm min-w-[240px]">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Progress</span>
                      <span className="text-[10px] font-bold text-brand-green">{Math.round(progress)}%</span>
                    </div>
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${progress}%` }}
                          transition={{ duration: 0.8 }}
                          className="h-full bg-brand-green" 
                        />
                    </div>
                  </div>
                  <div className="h-8 w-[1px] bg-slate-100"></div>
                  <div className="flex items-center gap-2 shrink-0">
                    <TrendingUp className="h-4 w-4 text-brand-blue" />
                    <span className="text-sm font-bold">{streak}d</span>
                  </div>
                </div>
              </div>

              {/* Phrase List */}
              <section className="space-y-6">
                <div className="flex items-center justify-between pt-4">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-1 bg-brand-blue rounded-full"></div>
                    <div>
                        <h3 className="text-lg font-bold tracking-tight">Today's Collection</h3>
                        <p className="text-xs font-medium text-slate-500">{format(new Date(), "MMMM d")}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {progress < 100 && (
                      <button 
                        onClick={markAllLearned}
                        className="text-[10px] font-bold uppercase tracking-widest text-brand-blue bg-blue-50 px-3 py-1.5 rounded-full border border-blue-100 hover:bg-brand-blue hover:text-white transition-all shadow-sm"
                      >
                        Mark All Learned
                      </button>
                    )}
                  </div>
                </div>

                {loading ? (
                  <div className="flex flex-col items-center justify-center py-20 text-slate-400 gap-4">
                    <motion.div 
                      animate={{ rotate: 360 }} 
                      transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                      className="h-10 w-10 text-brand-blue/40"
                    >
                      <Loader2 className="h-full w-full" />
                    </motion.div>
                    <p className="text-sm font-bold uppercase tracking-widest text-slate-400">Curating Today's Impact...</p>
                  </div>
                ) : (
                  <div className="grid gap-6">
                    {todayPhrases.length > 0 ? (
                      todayPhrases.map((phrase: Phrase, idx: number) => (
                        <PhraseCard 
                          key={phrase.phrase} 
                          phrase={phrase} 
                          index={idx}
                          isLearned={state.learnedPhrases.includes(phrase.phrase)}
                          onToggleLearned={() => toggleLearned(phrase.phrase)}
                        />
                      ))
                    ) : (
                      <div className="text-center py-20 rounded-2xl border border-dashed border-slate-200 bg-white">
                        <p className="text-slate-400 font-medium italic">Generating your learning session...</p>
                      </div>
                    )}
                  </div>
                )}
              </section>
            </motion.div>
          )}

          {view === "history" && (
            <motion.div
              key="history"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="space-y-6"
            >
              <div className="flex items-center gap-3">
                <div className="h-10 w-1 bg-brand-yellow rounded-full"></div>
                <div>
                    <h3 className="text-xl font-bold tracking-tight">The Library Archive</h3>
                    <p className="text-xs font-medium text-slate-500">Your collected professional wisdom</p>
                </div>
              </div>

              {state.history.length > 0 ? (
                <div className="flex flex-col gap-3">
                  {[...state.history].sort((a,b) => b.date.localeCompare(a.date)).map((day) => (
                    <motion.div 
                      key={day.date} 
                      whileHover={{ x: 4 }}
                      onClick={() => {
                        setTodayPhrases(day.phrases);
                        setView("home");
                      }}
                      className="group flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-4 transition-all hover:border-brand-blue cursor-pointer"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-24 shrink-0">
                           <div className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">{format(new Date(day.date), "MMM yyyy")}</div>
                           <div className="text-sm font-bold text-slate-900">{format(new Date(day.date), "MMMM d")}</div>
                        </div>
                        <div className="h-8 w-[1px] bg-slate-100 hidden sm:block"></div>
                        <div className="flex flex-wrap gap-2">
                          {day.phrases.map(p => (
                            <div 
                              key={p.phrase} 
                              title={p.phrase}
                              className="px-2.5 py-1 rounded-md bg-slate-50 text-[10px] font-semibold text-slate-600 border border-slate-100 transition-colors group-hover:bg-brand-blue/5 group-hover:text-brand-blue group-hover:border-brand-blue/10 max-w-[120px] truncate"
                            >
                              {p.phrase}
                            </div>
                          ))}
                        </div>
                      </div>
                      <div className="flex items-center justify-end">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-50 text-slate-400 group-hover:bg-brand-dark group-hover:text-white transition-all">
                          <ChevronRight className="h-4 w-4" />
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-32 text-slate-400 gap-4 rounded-3xl border border-dashed border-slate-200 bg-white">
                  <History className="h-10 w-10 opacity-20" />
                  <p className="text-sm font-bold uppercase tracking-widest">No archives found yet</p>
                </div>
              )}
            </motion.div>
          )}

          {view === "about" && (
            <motion.div
              key="about"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-8"
            >
              <section className="rounded-3xl border border-slate-200 bg-white p-8 sm:p-12 relative overflow-hidden">
                <div className="relative z-10 max-w-2xl">
                  <h2 className="text-4xl font-bold tracking-tight text-brand-dark leading-tight mb-6">
                    Professional fluency, <br /> simplified.
                  </h2>
                  <div className="space-y-4 text-lg font-medium text-slate-600 leading-relaxed">
                    <p>
                      Daily English is designed for the modern professional who doesn't have hours to spend in formal classes.
                    </p>
                    <p>
                      We use high-performance AI to curate five impactful expressions every single day. These aren't just vocabulary words; they are the keys to effective collaboration and confident leadership.
                    </p>
                  </div>

                  <div className="mt-12 grid gap-6 sm:grid-cols-2">
                    <div className="rounded-2xl bg-slate-50 p-6 border border-slate-100">
                      <BookOpen className="h-6 w-6 text-brand-blue mb-3" />
                      <h4 className="font-bold text-slate-900 mb-2">Focused Learning</h4>
                      <p className="text-sm font-medium text-slate-500 italic">
                        By limiting daily intake to five phrases, we ensure cognitive load stays manageable and retention remains high.
                      </p>
                    </div>
                    <div className="rounded-2xl bg-brand-dark p-6 text-white shadow-lg">
                      <TrendingUp className="h-6 w-6 text-brand-green mb-3" />
                      <h4 className="font-bold text-white mb-2">Compound Growth</h4>
                      <p className="text-sm font-medium text-slate-300">
                        Five phrases a day, every day, builds a massive high-impact vocabulary that transforms your professional presence.
                      </p>
                    </div>
                  </div>
                </div>
                <div className="absolute -right-10 -bottom-10 h-64 w-64 bg-slate-50 rounded-full blur-3xl -z-0"></div>
              </section>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer className="mt-12 border-t border-slate-200 py-10 bg-white">
        <div className="mx-auto max-w-5xl px-6 sm:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
               <div className="w-6 h-6 bg-brand-dark rounded flex items-center justify-center text-white font-bold text-[10px]">DE</div>
               <span className="font-bold tracking-tight text-sm uppercase">Daily English Pro</span>
            </div>
            <div className="flex gap-6 text-[10px] font-bold uppercase tracking-widest text-slate-400">
               <a href="#" className="hover:text-brand-blue transition-colors">Privacy</a>
               <a href="#" className="hover:text-brand-blue transition-colors">Terms</a>
            </div>
            <p className="text-[10px] text-slate-300 font-bold uppercase tracking-widest">
              Powered by Gemini AI · © 2026
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
