import { Action, ActionResWithUndefined, ActionsRes, ActionsResWithUndefined, Candidate } from '@/types/action';
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
    const nextStep = steps.at(currentStepIndex + 1);
    const currentStep = steps.at(currentStepIndex);
    if (currentStep == undefined) return err('ステップが存在しません');

    const { collectedStep, isNext } = correctCurrentStep(action, currentStep, nextStep);
    actionsResWithUndefined.push(toActionRes(action, collectedStep));

    if (isNext) currentStepIndex++;
  }

  const filledRes = fillUndefined(actionsResWithUndefined);
  if (!filledRes.success) return filledRes;

  const mergedActions = mergeContinuousSteps(filledRes.data);
  return ok(mergedActions);
}

/** 現在のステップの補正をする */
function correctCurrentStep(
  action: Action,
  currentStep: Step,
  nextStep: Step | undefined,
  threshold4alternative = 0.2,
): { collectedStep: Step | undefined; isNext: boolean } {
  const mostProbable = getNthMostProbable(action);
  if (mostProbable == undefined) return { collectedStep: undefined, isNext: false };

  // 推定結果が現在のステップと一致する場合は補正は不要
  if (mostProbable.processId == currentStep.processId) return { collectedStep: currentStep, isNext: false };

  // 推定結果が次のステップと一致する場合は次のステップに進む
  if (mostProbable.processId == nextStep?.processId) return { collectedStep: nextStep, isNext: true };

  // 現在/次のステップが確信度が閾値以上の推定結果がある場合はそのステップに進む
  for (const estimation of action.candidates) {
    if (estimation.probability >= threshold4alternative) continue;
    if (estimation.processId == currentStep.processId) return { collectedStep: currentStep, isNext: false };
    if (estimation.processId == nextStep?.processId) return { collectedStep: nextStep, isNext: true };
  }

  // 補正不可
  return { collectedStep: undefined, isNext: false };
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
function fillUndefined(actionsResWithUndefined: ActionsResWithUndefined): Result<ActionsRes> {
  const actionsRes: ActionsRes = [];
  const firstActionRes = actionsResWithUndefined.at(0);
  if (firstActionRes == undefined) return err('アクションが存在しません');

  if (firstActionRes?.step == undefined) return err('最初のステップは必須です');

  actionsRes.push({ ...firstActionRes, step: firstActionRes?.step });

  for (const current of actionsResWithUndefined) {
    const before = actionsRes.at(-1);
    if (before == undefined) return err('前のアクションが存在しません');

    const curretnStep = current?.step;
    if (current != undefined && curretnStep != undefined) {
      actionsRes.push({ ...current, step: curretnStep });
      continue;
    }

    actionsRes.push({ ...before, step: before.step });
  }

  return ok(actionsRes);
}

/** 同じ step が連続している場合は結合する */
function mergeContinuousSteps(actionsRes: ActionsRes): ActionsRes {
  const merged: ActionsRes = [];
  let before = actionsRes.at(0);
  if (before?.step == undefined) return actionsRes;

  for (const current of actionsRes) {
    if (current.step.processId !== before.step.processId) continue;
    if (current.step.requiredGroups !== before.step.requiredGroups) continue;

    const { start, step } = before;
    const { end } = current;
    merged.push({ start, end, step });

    before = current;
  }

  return merged;
}
