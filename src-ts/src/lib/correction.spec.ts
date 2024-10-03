import { ActionsRes, ActionsResWithUndefined } from '@/types/action';
import { describe, expect, test } from 'vitest';
import { fillUndefined, mergeContinuousSteps } from './correction';

describe('correction', () => {
  describe('fillUndefined', () => {
    test('[正常系] 補正できなかった部分を埋めれるか', () => {
      const actionsResWithUndefined: ActionsResWithUndefined = [
        {
          start: 0,
          end: 1,
          step: {
            title: 'title',
            processId: 'PROCESS[1]',
            requiredGroups: [],
            required: [],
            time: { hour: 0, minute: 0, second: 0 },
          },
        },
        {
          start: 0,
          end: 1,
          step: undefined,
        },
      ];

      const result = fillUndefined(actionsResWithUndefined);
      if (!result.success) throw new Error('fillUndefined に失敗しました');

      expect(result.data[1]?.step).toBeDefined();
      expect(result.data[1]?.step?.processId).toBe(actionsResWithUndefined[0]?.step?.processId);
    });
  });

  describe('mergeContinuousSteps', () => {
    test('[正常系] 連続するステップをマージできるか', () => {
      const actionsRes: ActionsRes = [
        {
          start: 0,
          end: 1,
          step: {
            title: 'same',
            processId: 'PROCESS[1]',
            requiredGroups: [],
            required: [],
            time: { hour: 0, minute: 0, second: 0 },
          },
        },
        {
          start: 1,
          end: 2,
          step: {
            title: 'same',
            processId: 'PROCESS[1]',
            requiredGroups: [],
            required: [],
            time: { hour: 0, minute: 0, second: 0 },
          },
        },
        {
          start: 2,
          end: 3,
          step: {
            title: 'not same',
            processId: 'PROCESS[1]',
            requiredGroups: [],
            required: [],
            time: { hour: 0, minute: 0, second: 0 },
          },
        },
      ];

      const result = mergeContinuousSteps(actionsRes);
      expect(result).toHaveLength(2);
      expect(result[0]?.start).toBe(actionsRes[0]?.start);
      expect(result[0]?.end).toBe(actionsRes[1]?.end);
      expect(result[0]?.step).toEqual(actionsRes[0]?.step);
    });
  });
});
