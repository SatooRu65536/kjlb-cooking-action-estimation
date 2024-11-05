import { Action, ActionsRes, ActionsResWithUndefined } from "@/types/action";
import { describe, expect, test } from "vitest";
import {
  collectActions,
  fillUndefined,
  mergeContinuousSteps,
} from "./correction";
import { Step } from "@/types/recipe";

describe("correction", () => {
  describe("collectActions", () => {
    test("[正常系] collectActions が正常に動作するか", () => {
      const actions: Action[] = [
        // そのまま
        {
          start: 0,
          end: 1,
          candidates: [
            {
              processId: "PROCESS[0]",
              probability: 0.9,
              label: 0,
            },
            {
              processId: "PROCESS[1]",
              probability: 0.1,
              label: 1,
            },
          ],
        },
        // 次のステップ
        {
          start: 1,
          end: 2,
          candidates: [
            {
              processId: "PROCESS[1]",
              probability: 0.8,
              label: 1,
            },
            {
              processId: "PROCESS[0]",
              probability: 0.1,
              label: 0,
            },
          ],
        },
        // candidates の 2番目
        {
          start: 2,
          end: 3,
          candidates: [
            {
              processId: "PROCESS[0]",
              probability: 0.7,
              label: 1,
            },
            {
              processId: "PROCESS[1]",
              probability: 0.3,
              label: 0,
            },
          ],
        },
        // スキップ
        {
          start: 3,
          end: 4,
          candidates: [
            {
              processId: "PROCESS[skip]",
              probability: 0.7,
              label: 1,
            },
          ],
        },
        // そのまま
        {
          start: 4,
          end: 5,
          candidates: [
            {
              processId: "PROCESS[1]",
              probability: 1,
              label: 1,
            },
          ],
        },
        // そのまま
        {
          start: 5,
          end: 6,
          candidates: [
            {
              processId: "PROCESS[1]",
              probability: 1,
              label: 1,
            },
          ],
        },
        // スキップ (推定誤り: 本来はPROCESS[2])
        {
          start: 6,
          end: 7,
          candidates: [
            {
              processId: "PROCESS[skip_error]",
              probability: 1,
              label: 1,
            },
          ],
        },
        // スキップの本来の工程を飛ばす
        {
          start: 7,
          end: 8,
          candidates: [
            {
              processId: "PROCESS[3]",
              probability: 1,
              label: 1,
            },
          ],
        },
      ];
      const steps: Step[] = [
        {
          processId: "PROCESS[0]",
          title: "1つめ",
          requiredGroups: [],
          required: [],
        },
        {
          processId: "PROCESS[1]",
          title: "2つめ",
          requiredGroups: [],
          required: [],
        },
        {
          processId: "PROCESS[2]",
          title: "3つめ",
          requiredGroups: [],
          required: [],
        },
        {
          processId: "PROCESS[3]",
          title: "4つめ",
          requiredGroups: [],
          required: [],
        },
      ];

      // 正解のactions
      const correctActions: ActionsRes = [
        {
          start: 0,
          end: 1,
          step: {
            processId: "PROCESS[0]",
            title: "1つめ",
            required: [],
            requiredGroups: [],
          },
        },
        {
          start: 1,
          end: 6,
          step: {
            processId: "PROCESS[1]",
            title: "2つめ",
            required: [],
            requiredGroups: [],
          },
        },
        {
          start: 6,
          end: 7,
          step: {
            processId: "PROCESS[2]",
            title: "3つめ",
            required: [],
            requiredGroups: [],
          },
        },
        {
          start: 7,
          end: 8,
          step: {
            processId: "PROCESS[3]",
            title: "4つめ",
            required: [],
            requiredGroups: [],
          },
        },
      ];

      const res = collectActions(actions, steps);

      if (!res.success) throw new Error("collectActions に失敗しました");
      expect(res.data).toBeDefined();
      expect(res.data).toEqual(correctActions);
    });
  });

  describe("fillUndefined", () => {
    test("[正常系] 直前のactionで埋める", () => {
      const actionsResWithUndefined: ActionsResWithUndefined = [
        {
          start: 0,
          end: 1,
          step: {
            title: "title",
            processId: "PROCESS[1]",
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

      const result = fillUndefined(actionsResWithUndefined, []);
      if (!result.success) throw new Error("fillUndefined に失敗しました");

      expect(result.data[1]?.step).toBeDefined();
      expect(result.data[1]?.step?.processId).toBe(
        actionsResWithUndefined[0]?.step?.processId,
      );
    });

    test("[正常系] 飛ばされた工程で埋める", () => {
      const actionsResWithUndefined: ActionsResWithUndefined = [
        {
          start: 0,
          end: 1,
          step: {
            title: "title",
            processId: "PROCESS[1]",
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
        {
          start: 0,
          end: 1,
          step: {
            title: "title",
            processId: "PROCESS[3]",
            requiredGroups: [],
            required: [],
            time: { hour: 0, minute: 0, second: 0 },
          },
        },
      ];
      const steps: Step[] = [
        {
          processId: "PROCESS[1]",
          title: "title",
          requiredGroups: [],
          required: [],
          time: { hour: 0, minute: 0, second: 0 },
        },
        {
          processId: "PROCESS[2]",
          title: "title",
          requiredGroups: [],
          required: [],
          time: { hour: 0, minute: 0, second: 0 },
        },
        {
          processId: "PROCESS[3]",
          title: "title",
          requiredGroups: [],
          required: [],
          time: { hour: 0, minute: 0, second: 0 },
        },
      ];

      const result = fillUndefined(actionsResWithUndefined, steps);
      if (!result.success) throw new Error("fillUndefined に失敗しました");

      expect(result.data[1]?.step).toBeDefined();
      expect(result.data[1]?.step?.processId).toBe(steps[1]?.processId);
    });

    test("[正常系] 連続で飛ばされた工程で埋める", () => {
      const actionsResWithUndefined: ActionsResWithUndefined = [
        {
          start: 0,
          end: 1,
          step: {
            title: "title",
            processId: "PROCESS[1]",
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
        {
          start: 0,
          end: 1,
          step: undefined,
        },
        {
          start: 0,
          end: 1,
          step: {
            title: "title",
            processId: "PROCESS[4]",
            requiredGroups: [],
            required: [],
            time: { hour: 0, minute: 0, second: 0 },
          },
        },
      ];
      const steps: Step[] = [
        {
          processId: "PROCESS[1]",
          title: "title",
          requiredGroups: [],
          required: [],
          time: { hour: 0, minute: 0, second: 0 },
        },
        {
          processId: "PROCESS[2]",
          title: "title",
          requiredGroups: [],
          required: [],
          time: { hour: 0, minute: 0, second: 0 },
        },
        {
          processId: "PROCESS[3]",
          title: "title",
          requiredGroups: [],
          required: [],
          time: { hour: 0, minute: 0, second: 0 },
        },
        {
          processId: "PROCESS[4]",
          title: "title",
          requiredGroups: [],
          required: [],
          time: { hour: 0, minute: 0, second: 0 },
        },
      ];

      const result = fillUndefined(actionsResWithUndefined, steps);
      if (!result.success) throw new Error("fillUndefined に失敗しました");

      expect(result.data[1]?.step).toBeDefined();
      expect(result.data[1]?.step?.processId).toBe(steps[1]?.processId);
      expect(result.data[2]?.step).toBeDefined();
      expect(result.data[2]?.step?.processId).toBe(steps[2]?.processId);
    });
  });

  describe("mergeContinuousSteps", () => {
    test("[正常系] 連続するステップをマージできるか", () => {
      const actionsRes: ActionsRes = [
        {
          start: 0,
          end: 1,
          step: {
            title: "same",
            processId: "PROCESS[1]",
            requiredGroups: [],
            required: [],
            time: { hour: 0, minute: 0, second: 0 },
          },
        },
        {
          start: 1,
          end: 2,
          step: {
            title: "same",
            processId: "PROCESS[1]",
            requiredGroups: [],
            required: [],
            time: { hour: 0, minute: 0, second: 0 },
          },
        },
        {
          start: 2,
          end: 3,
          step: {
            title: "not same",
            processId: "PROCESS[1]",
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
