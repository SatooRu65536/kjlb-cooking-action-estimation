import {
  Action,
  ActionRes,
  ActionResWithUndefined,
  ActionsRes,
  ActionsResWithUndefined,
  Candidate,
} from '@/types/action';
import { Step } from '@/types/recipe';
import { Result } from '@/types/result';
import { err, ok } from '@/utils/result';

/** 推定結果を補正する */
export function collectActions(actions: Action[], steps: Step[]): Result<ActionsRes> {
  let currentStepIndex = 0;

  const firstAction = actions.at(0);
  if (firstAction == undefined) return err('アクションが存在しません');
  const firstStep = steps.at(0);
  if (firstStep == undefined) return err('ステップが存在しません');

  const actionsResWithUndefined: ActionsResWithUndefined = [
    {
      start: firstAction.start,
      end: firstAction.end,
      step: firstStep,
    },
  ];
  for (const action of actions.slice(1)) {
    const futureSteps = steps.slice(currentStepIndex + 1);
    const currentStep = steps.at(currentStepIndex);
    if (currentStep == undefined) return err('ステップが存在しません');

    const { collectedStep, plsStepIndex } = correctCurrentStep(
      action,
      currentStep,
      futureSteps,
      actionsResWithUndefined,
    );
    actionsResWithUndefined.push(toActionRes(action, collectedStep));

    currentStepIndex += plsStepIndex;
  }

  const filledRes = fillUndefined(actionsResWithUndefined, steps);
  if (!filledRes.success) return filledRes;

  const mergedActions = mergeContinuousSteps(filledRes.data);
  return ok(mergedActions);
}

/** 現在のステップの補正をする */
function correctCurrentStep(
  action: Action,
  currentStep: Step,
  futureSteps: Step[],
  actionsResWithUndefined: ActionsResWithUndefined,
  threshold4alternative = 0.2,
): { collectedStep: Step | undefined; plsStepIndex: number } {
  const nextStep = futureSteps.at(0);
  const mostProbable = getNthMostProbable(action);
  if (mostProbable == undefined) return { collectedStep: undefined, plsStepIndex: 0 };

  // 推定結果が現在のステップと一致する場合は補正は不要
  if (mostProbable.processId == currentStep.processId) return { collectedStep: currentStep, plsStepIndex: 0 };

  // 推定結果が次のステップと一致する場合は次のステップに進む
  if (mostProbable.processId == nextStep?.processId) return { collectedStep: nextStep, plsStepIndex: 1 };

  // 直前に undefined が続いている数
  let undefinedCount = 0;
  for (const action of structuredClone(actionsResWithUndefined).reverse()) {
    if (action.step != undefined) break;
    undefinedCount++;
  }
  for (let i = 0; i < undefinedCount; i++) {
    const step = futureSteps.at(i + 1);
    if (step == undefined) continue;

    if (mostProbable.processId == step.processId) return { collectedStep: step, plsStepIndex: i + 1 };
  }

  // 現在/次のステップが確信度が閾値以上の推定結果がある場合はそのステップに進む
  for (const estimation of action.candidates) {
    if (estimation.probability < threshold4alternative) continue;
    if (estimation.processId == currentStep.processId) return { collectedStep: currentStep, plsStepIndex: 0 };
    if (estimation.processId == nextStep?.processId) return { collectedStep: nextStep, plsStepIndex: 1 };
  }

  // 補正不可
  return { collectedStep: undefined, plsStepIndex: 0 };
}

/** n番目に確信度が高い推定結果を取得する. 省略時は最も確信度が高い推定結果を取得する */
function getNthMostProbable(action: Action, n?: number): Candidate | undefined {
  const sorted = action.candidates.sort((a, b) => b.probability - a.probability);
  return sorted.at(n ?? 0);
}

/** action と step から actionRes に変換する */
function toActionRes(action: Action, step: Step | undefined): ActionResWithUndefined {
  const { start, end } = action;
  return { start, end, step };
}

/** 補正できなかった部分を埋める */
export function fillUndefined(actionsResWithUndefined: ActionsResWithUndefined, steps: Step[]): Result<ActionsRes> {
  const actionsRes: ActionsRes = [];
  const firstActionRes = actionsResWithUndefined.at(0);
  if (firstActionRes == undefined) return err('アクションが存在しません');

  if (firstActionRes?.step == undefined) return err('最初のステップは必須です');

  actionsRes.push({ ...firstActionRes, step: firstActionRes?.step });

  for (let i = 1; i < actionsResWithUndefined.length; i++) {
    const prev = actionsRes.at(-1);
    if (prev == undefined) return err('前のアクションが存在しません');
    const current = actionsResWithUndefined.at(i);
    if (current == undefined) return err('現在のアクションが存在しません');
    const afterActions = actionsResWithUndefined.slice(i + 1);

    // 現在の工程が存在する場合はそのまま追加
    const curretnStep = current?.step;
    if (curretnStep != undefined) {
      actionsRes.push({ ...current, step: curretnStep });
      continue;
    }

    // 抜けている工程を入れる
    const missingSteps = getMissingSteps(prev, afterActions, steps);
    if (missingSteps != undefined) {
      actionsRes.push({ ...current, step: missingSteps });
      continue;
    }

    // 前の工程を入れる
    actionsRes.push({ ...prev, step: prev.step });
  }

  return ok(actionsRes);
}

/** 抜けている工程を取得する */
function getMissingSteps(prev: ActionRes, afterActions: ActionResWithUndefined[], steps: Step[]): Step | undefined {
  const prevStepIndex = steps.findIndex((s) => s.processId == prev.step.processId);
  const nextStep = afterActions.find((a) => a.step != undefined)?.step;
  const nextStepIndex =
    nextStep == undefined ? steps.length : steps.findIndex((s) => s.processId == nextStep?.processId);

  const missingSteps = steps.slice(prevStepIndex + 1, nextStepIndex);
  return missingSteps.at(0);
}

/** 同じ step が連続している場合は結合する */
export function mergeContinuousSteps(actionsRes: ActionsRes): ActionsRes {
  const clonedActionsRes = structuredClone(actionsRes);

  const firstActionRes = clonedActionsRes.at(0);
  if (firstActionRes?.step == undefined) throw new Error('最初のステップは必須です');

  const merged: ActionsRes = [firstActionRes];
  let prev = clonedActionsRes.at(0);
  if (prev?.step == undefined) return clonedActionsRes;

  for (const current of clonedActionsRes.slice(1)) {
    if (isSameStep(prev.step, current.step)) {
      const pop = merged.pop();
      if (pop == undefined) throw new Error('pop に失敗しました');
      merged.push({ ...pop, end: current.end });
    } else {
      merged.push(current);
    }
    prev = current;
  }

  return merged;
}

/** 同じ step か */
function isSameStep(a: Step, b: Step): boolean {
  if (a.processId !== b.processId) return false;
  if (a.title !== b.title) return false;
  if (a.time?.hour !== b.time?.hour) return false;
  if (a.time?.minute !== b.time?.minute) return false;
  if (a.time?.second !== b.time?.second) return false;
  if (!a.required.every((r) => b.required.includes(r))) return false;
  if (!a.requiredGroups.every((r) => b.requiredGroups.includes(r))) return false;

  return true;
}
