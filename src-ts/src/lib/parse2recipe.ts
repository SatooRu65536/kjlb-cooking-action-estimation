import { Recipe, RecipeYaml, Step, Time } from '@/types/recipe';
import { load } from 'js-yaml';
import { readFileSync, existsSync } from 'node:fs';
import { zRecipeYaml } from '@/schema/recipe';
import { Result } from '@/types/result';
import { err, ok } from '@/utils/result';

/** 指定したパスのyamlファイルを読み込んでRecipeに変換する */
export function parse2recipe(path: string): Result<Recipe> {
  const readRes = readYaml(path);
  if (readRes.success === false) return readRes;

  const validateRes = validateRecipe(readRes.data);
  if (!validateRes.success) return err(validateRes.error);

  return recipeYaml2Recipe(validateRes.data);
}

/** RecipeYaml を Recipe に変換する */
function recipeYaml2Recipe(recipeYaml: RecipeYaml): Result<Recipe> {
  const { name, url, ingredients, steps: yamlSteps, processes } = recipeYaml;

  try {
    const steps = yamlSteps.map((step) => {
      const process = processes.find((p) => p.id === step.process);
      if (process == undefined) throw new Error('Process not found');

      const processId = step.process;
      const time = step.time ? parseTime(step.time) : parseTime(process.time);
      const title = process.title;
      const required = (step.required ?? process.required ?? []).map((r) => r.id);
      const requiredGroups = step.required_groups ?? [];

      return { processId, title, time, required, requiredGroups } satisfies Step;
    });

    return ok({ name, url, ingredients, steps } satisfies Recipe);
  } catch (error: unknown) {
    if (error instanceof Error) return err(error.message);
    return err('Unknown error');
  }
}

/** 文字列の time を構造化する */
function parseTime(time: string | undefined): Time {
  if (time == undefined) return undefined;

  const [hour, minute, second] = time.split(':').map(Number);

  if (Number.isNaN(hour)) throw new Error('Invalid time format');
  if (Number.isNaN(minute)) throw new Error('Invalid time format');
  if (Number.isNaN(second)) throw new Error('Invalid time format');

  return { hour, minute, second } satisfies Time;
}

/** バリデーションする */
function validateRecipe(content: unknown): Result<RecipeYaml> {
  const res = zRecipeYaml.safeParse(content);
  if (!res.success) return err(res.error.message);
  return ok(res.data);
}

/** yamlファイルを読み込む */
function readYaml(path: string): Result<unknown> {
  if (!existsSync(path)) return err(`File not found: ${path}`);
  const content = load(readFileSync(path, 'utf8'));
  return ok(content);
}
