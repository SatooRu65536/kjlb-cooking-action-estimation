import { describe, expect, test } from 'vitest';
import { checkRecipe } from './check-recipe';
import { Recipe } from '@/types/recipe';

describe('check', () => {
  test('requiredGroups が重複していないか', () => {
    const recipe: Recipe = {
      name: 'グループが重複',
      ingredients: [],
      steps: [
        {
          processId: 'PROCESS[重複]',
          title: '重複',
          required: [],
          requiredGroups: ['GROUP[重複]', 'GROUP[重複]'],
        },
      ],
    };

    const res = checkRecipe(recipe);

    if (res.success) throw new Error('requiredGroups の重複を検知できていません');
    expect(res.success).toBe(false);
    expect(res.error).toBe('Duplicate required group GROUP[重複]');
  });

  test('requiredGroups がループしていないか', () => {
    const recipe: Recipe = {
      name: 'グループが重複',
      ingredients: [],
      steps: [
        {
          processId: 'PROCESS[1]',
          title: '重複',
          required: ['PROCESS[2]'],
          requiredGroups: ['GROUP[1]'],
        },
        {
          processId: 'PROCESS[2]',
          title: '重複',
          required: ['PROCESS[1]'],
          requiredGroups: ['GROUP[1]'],
        },
      ],
    };

    const res = checkRecipe(recipe);

    if (res.success) throw new Error('requiredGroups のループを検知できていません');
    expect(res.success).toBe(false);
    expect(res.error).toBe('Loop detected PROCESS[1]');
  });

  test('存在しない processId が指定されていないか', () => {
    const recipe: Recipe = {
      name: 'グループが重複',
      ingredients: [],
      steps: [
        {
          processId: 'PROCESS[1]',
          title: '重複',
          required: ['PROCESS[2]'],
          requiredGroups: ['GROUP[1]'],
        },
      ],
    };

    const res = checkRecipe(recipe);

    if (res.success) throw new Error('存在しない processId を検知できていません');
    expect(res.success).toBe(false);
    expect(res.error).toBe('ProcessId not found PROCESS[2]');
  });
});
