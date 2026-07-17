/**
 * Generate page TypeScript source.
 * 运行时逻辑见 frontend/js/generate.js（与本文件语义同步）。
 */

export interface ResumePayload {
  template_id: string;
  name: string;
  phone: string;
  email: string;
  summary: string;
  skills: string;
  photo_path: string;
  experiences: {
    company: string;
    period: string;
    title: string;
    description: string;
  }[];
  education: {
    school: string;
    period: string;
    degree: string;
    major: string;
  }[];
  projects: {
    name: string;
    period: string;
    description: string;
  }[];
}

declare const ResumeBridge: {
  apiCall: <T = unknown>(method: string, ...args: unknown[]) => Promise<T>;
  showToast: (msg: string, type?: string) => void;
};