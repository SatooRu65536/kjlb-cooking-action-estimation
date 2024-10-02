import { describe, expect, test } from 'vitest';
import { parse2recipe } from './parse2recipe';
import { zRecipe } from '@/schema/recipe';

describe('parse2recipe', () => {
  test('レシビをパースできるか', () => {
    const res = parse2recipe('../recipes/data/rolled_omelet.yaml');

    if (!res.success) throw new Error(res.error);

    expect(res.data).toBeDefined();
    expect(zRecipe.safeParse(res.data)).toEqual({ success: true, data: res.data });
  });
});
