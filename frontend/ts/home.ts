/**
 * Home page TypeScript source (逻辑同步见 frontend/js/home.js)
 */

declare const ResumeBridge: {
  apiCall: <T = unknown>(method: string, ...args: unknown[]) => Promise<T>;
  showToast: (msg: string, type?: string) => void;
  waitForApi: (timeoutMs?: number) => Promise<boolean>;
};

export function greetingLabel(date = new Date()): string {
  const h = date.getHours();
  if (h < 12) return "上午好";
  if (h < 18) return "下午好";
  return "晚上好";
}