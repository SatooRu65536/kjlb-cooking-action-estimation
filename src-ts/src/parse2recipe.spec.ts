import { describe, expect, test } from 'vitest';
import { parse2recipe } from './parse2recipe';

describe('parse2recipe', () => {
  test('should return a recipe object', () => {
    const res = parse2recipe('../recipes/data/rolled_omelet.yaml');

    if (!res.success) throw new Error(res.error);

    console.log(JSON.stringify(res.data, undefined, 2));
    expect(res.data).toBeDefined();
  });
});
