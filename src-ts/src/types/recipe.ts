import { zProcessId, zIngredient, zStep, zRecipe, zRecipeYaml, zTime, zGroupID } from '@/schema/recipe';
import { z } from 'zod';

export type ProcessId = z.infer<typeof zProcessId>;
export type GroupID = z.infer<typeof zGroupID>;
export type Time = z.infer<typeof zTime>;
export type Ingredient = z.infer<typeof zIngredient>;
export type Step = z.infer<typeof zStep>;
export type Recipe = z.infer<typeof zRecipe>;
export type RecipeYaml = z.infer<typeof zRecipeYaml>;
