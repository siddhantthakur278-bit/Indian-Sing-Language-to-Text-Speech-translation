/**
 * API Client for Sentence Translation Proxy
 */

export interface SentenceRequest {
  glosses: string[];
  lang: string;
}

export interface SentenceResponse {
  sentence: string;
  translated: string;
  lang: string;
  emergency: boolean;
  audio_url: string | null;
}

export async function requestSentenceTranslation(
  glosses: string[],
  lang: string = "hi"
): Promise<SentenceResponse> {
  const response = await fetch("/api/sentence", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ glosses, lang }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `Server error: ${response.status}`);
  }

  return response.json();
}
