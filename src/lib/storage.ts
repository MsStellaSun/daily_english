
import { AppState, DailyData } from "../types";

const STORAGE_KEY = "daily_english_pro_state";

export const loadState = (): AppState => {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch {
      // fallback
    }
  }
  return { history: [], learnedPhrases: [] };
};

export const saveState = (state: AppState) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
};

export const getTodayData = (history: DailyData[]): DailyData | undefined => {
  const today = new Date().toISOString().split("T")[0];
  return history.find((d) => d.date === today);
};
