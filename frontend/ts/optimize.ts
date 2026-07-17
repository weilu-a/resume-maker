/**
 * Optimize page TypeScript source (逻辑同步见 frontend/js/optimize.js)
 * 本文件作为课程要求的 TS 源码保留；运行时加载编译后的 JS。
 */

declare const ResumeBridge: {
  apiCall: <T = unknown>(method: string, ...args: unknown[]) => Promise<T>;
  showToast: (msg: string, type?: string) => void;
  waitForApi: (timeoutMs?: number) => Promise<boolean>;
};

export interface OptimizeSection {
  title: string;
  content: string;
}

export interface OptimizeResult {
  ok?: boolean;
  error?: string;
  ai_source?: string;
  score?: number;
  skill_match?: number;
  experience_density?: number;
  keywords?: number;
  score_up?: number;
  original_sections?: OptimizeSection[];
  optimized_sections?: OptimizeSection[];
  suggestions?: { type: string; icon: string; text: string }[];
}