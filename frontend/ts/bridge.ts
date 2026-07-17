/**
 * pywebview API bridge（TypeScript 源码说明）
 * 运行时请加载 frontend/js/bridge.js，它会挂载全局 `ResumeBridge`。
 */

export interface ApiResult {
  ok?: boolean;
  error?: string;
  [key: string]: unknown;
}

declare global {
  interface Window {
    pywebview?: {
      api: Record<string, (...args: unknown[]) => Promise<unknown>>;
    };
    ResumeBridge?: {
      showToast: (message: string, type?: string) => void;
      waitForApi: (timeoutMs?: number) => Promise<boolean>;
      apiCall: <T = unknown>(method: string, ...args: unknown[]) => Promise<T>;
    };
  }
}

/** 与 js/bridge.js 行为一致的类型约定 */
export type ResumeBridgeApi = NonNullable<Window["ResumeBridge"]>;