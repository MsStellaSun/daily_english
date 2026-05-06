
import { motion } from "motion/react";
import { CheckCircle2, Quote, Lightbulb, BookOpen } from "lucide-react";
import { Phrase } from "../types";

interface PhraseCardProps {
  phrase: Phrase;
  isLearned: boolean;
  onToggleLearned: () => void;
  index: number;
  key?: string | number;
}

export function PhraseCard({ phrase, isLearned, onToggleLearned, index }: PhraseCardProps) {
  const colorClass = "bg-white border-slate-200 hover:border-brand-blue/30";

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.05 }}
      className={`group relative overflow-hidden rounded-2xl border p-6 transition-all hover:shadow-sm ${
        isLearned ? "bg-slate-50 opacity-60 grayscale" : colorClass
      }`}
    >
      <div className="flex items-start justify-between mb-4">
        <span className={`inline-flex items-center rounded-full bg-brand-dark px-3 py-1 text-[10px] font-bold text-white uppercase tracking-wider`}>
          {phrase.category}
        </span>
        <button
          onClick={onToggleLearned}
          className={`flex h-8 w-8 items-center justify-center rounded-full transition-all ${
            isLearned ? "bg-brand-green text-white" : "bg-white text-slate-300 border border-slate-200 hover:border-brand-green hover:text-brand-green"
          }`}
        >
          <CheckCircle2 className="h-5 w-5" />
        </button>
      </div>

      <div className="space-y-4">
        <div>
          <h3 className={`text-2xl font-bold tracking-tight ${isLearned ? "text-slate-500 line-through" : "text-brand-dark"}`}>
            {phrase.phrase}
          </h3>
          <p className="mt-1 text-base font-medium text-slate-600 leading-relaxed">{phrase.meaning}</p>
        </div>

        <div className="grid gap-3 pt-2">
          <div className="flex flex-col gap-2">
            <div className="rounded-xl bg-white/60 p-4 text-sm font-medium text-slate-700 border border-slate-200/50 relative">
              <span className="absolute -top-2 left-3 bg-white px-2 py-0.5 text-[9px] font-bold uppercase tracking-tighter text-slate-400 border border-slate-100 rounded-full">Example 1</span>
              "{phrase.example1}"
            </div>
            <div className="rounded-xl bg-white/60 p-4 text-sm font-medium text-slate-700 border border-slate-200/50 relative">
              <span className="absolute -top-2 left-3 bg-white px-2 py-0.5 text-[9px] font-bold uppercase tracking-tighter text-slate-400 border border-slate-100 rounded-full">Example 2</span>
              "{phrase.example2}"
            </div>
          </div>

          <div className="mt-2 flex items-start gap-3 rounded-xl bg-brand-dark/[0.03] p-4 border border-brand-dark/5">
            <Lightbulb className="h-5 w-5 text-brand-yellow shrink-0 mt-0.5" />
            <p className="text-sm font-medium text-slate-600 leading-relaxed">
              {phrase.tip}
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
