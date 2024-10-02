import { zID, zIngredient, zStep, zRecipe, zRecipeYaml, zTime } from '@/schema/recipe';
import { z } from 'zod';

export type ID = z.infer<typeof zID>;
export type Time = z.infer<typeof zTime>;
export type Ingredient = z.infer<typeof zIngredient>;
export type Step = z.infer<typeof zStep>;
export type Recipe = z.infer<typeof zRecipe>;
export type RecipeYaml = z.infer<typeof zRecipeYaml>;
