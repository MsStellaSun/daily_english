
export interface Phrase {
  phrase: string;
  category: string;
  meaning: string;
  example1: string;
  example2: string;
  tip: string;
}

export interface DailyData {
  date: string; // YYYY-MM-DD
  phrases: Phrase[];
}

export interface AppState {
  history: DailyData[];
  learnedPhrases: string[]; // List of phrases the user marked as learned
}
