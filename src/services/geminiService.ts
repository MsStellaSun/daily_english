
import { GoogleGenAI, Type } from "@google/genai";
import { Phrase } from "../types";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

const SYSTEM_INSTRUCTION = `
Generate exactly 5 candidate English phrases for professional corporate communication.
The phrases should be practical, work-relevant, and commonly used in international business environments.

Generate a mix of:
- SHORT fragments (1-5 words): idiomatic chunks, verb phrases, prepositional phrases.
- LONGER phrases (6-15 words): complete expressions with context.

Categories:
- Meetings
- Email & Writing
- Polite Disagreement
- Presenting Ideas
- Clarification
- Transitions & Wrap-up

Return a JSON object with a 'phrases' array.
Each phrase must have: phrase, category, meaning, example1, example2, tip.
`;

export async function generateDailyPhrases(): Promise<Phrase[]> {
  try {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: "Generate today's 5 professional English phrases.",
      config: {
        systemInstruction: SYSTEM_INSTRUCTION,
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            phrases: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  phrase: { type: Type.STRING },
                  category: { type: Type.STRING },
                  meaning: { type: Type.STRING },
                  example1: { type: Type.STRING },
                  example2: { type: Type.STRING },
                  tip: { type: Type.STRING },
                },
                required: ["phrase", "category", "meaning", "example1", "example2", "tip"],
              },
            },
          },
          required: ["phrases"],
        },
      },
    });

    const data = JSON.parse(response.text);
    return data.phrases;
  } catch (error) {
    console.error("Error generating phrases:", error);
    throw error;
  }
}
