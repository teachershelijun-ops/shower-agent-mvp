/**
 * PromptBuilder - 占位文件
 * 后续用于根据花洒类型、Shot 索引等构建生成 Prompt
 */

export type ShowerType =
  | "Boost"
  | "LargePanel"
  | "Filter"
  | "TravelFilter"
  | "Descale";

export function buildPrompt(
  showerType: ShowerType,
  shotIndex: number,
  context?: Record<string, unknown>
): string {
  // TODO: 实现 Prompt 构建逻辑，对接 ShowerSkillLibrary
  return `[Placeholder] ShowerType=${showerType}, ShotIndex=${shotIndex}`;
}
