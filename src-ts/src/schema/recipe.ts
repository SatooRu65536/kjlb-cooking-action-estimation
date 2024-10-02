import { z } from 'zod';

export const zProcessId = z.string().regex(/^PROCESS\[.+]$/, 'failed to match ID pattern');
export const zGroupID = z.string().regex(/^GROUP\[.+]$/, 'failed to match GroupID pattern');

export const zTime = z
  .object({
    hour: z.number().min(0).max(23),
    minute: z.number().min(0).max(59),
    second: z.number().min(0).max(59),
  })
  .strict()
  .optional();

export const zIngredient = z
  .object({
    name: z.string(),
    quantity: z.number().gt(0),
    unit: z.string(),
  })
  .strict();

export const zStep = z
  .object({
    processId: zProcessId,
    title: z.string(),
    time: zTime,
    required: z.array(zProcessId),
    requiredGroup: zGroupID.optional(),
  })
  .strict();

export const zRecipe = z
  .object({
    name: z.string(),
    url: z.string().optional(),
    ingredients: z.array(zIngredient),
    steps: z.array(zStep),
  })
  .strict();

const zRawTime = z.string().regex(/^\d+:\d+:\d+$/);
const zRawStep = z
  .object({
    process: zProcessId,
    time: zRawTime.optional(),
    required: z.array(z.object({ id: zProcessId })).optional(),
    required_group: zGroupID.optional(),
  })
  .strict();
const zRawProcess = z
  .object({
    id: zProcessId,
    title: z.string(),
    time: zRawTime.optional(),
    required: z.array(z.object({ id: zProcessId })).optional(),
  })
  .strict();

export const zRecipeYaml = z.object({
  name: z.string(),
  url: z.string().url().optional(),
  ingredients: z.array(zIngredient),
  steps: z.array(zRawStep),
  processes: z.array(zRawProcess),
});
