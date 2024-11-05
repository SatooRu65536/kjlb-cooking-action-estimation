import { GroupID, ProcessId, Recipe } from "@/correction/types/recipe";
import { Result } from "@/correction/types/result";
import { err, ok } from "@/correction/utils/result";

/** Recipe を チェック する */
export function checkRecipe(recipe: Recipe): Result<true> {
  return checkRequired(recipe);
}

/**
 * Recipe の required をチェックする
 *
 * - 同一 step で グループID が重複していないか
 * - グループID が循環していないか
 * - 存在しない processId が指定されていないか
 */
function checkRequired(recipe: Recipe): Result<true> {
  // required を辿って processId を取得する関数
  const getProcessId = (
    processIds: ProcessId[],
    requiredGroups: GroupID[],
    stackedProcessIds: ProcessId[],
  ): Result<true> => {
    const duplicateGroup = requiredGroups.find(
      (g, i) => requiredGroups.indexOf(g) !== i,
    );
    if (duplicateGroup)
      return err(`Duplicate required group ${duplicateGroup}`);

    for (const processId of processIds) {
      const targetStep = recipe.steps.find(
        (s) =>
          s.processId === processId &&
          s.requiredGroups.some((g) => requiredGroups.includes(g)),
      );

      if (targetStep == undefined)
        return err(`ProcessId not found ${processId}`);

      const duplicateProcessId = targetStep.required.find(
        (id, i) => targetStep.required.indexOf(id) !== i,
      );
      if (duplicateProcessId)
        return err(`Duplicate required processId ${duplicateProcessId}`);

      const stackedProcessIds_ = [...targetStep.required, ...stackedProcessIds];

      const loopProcessId = stackedProcessIds_.find(
        (id, i) => stackedProcessIds_.indexOf(id) !== i,
      );
      if (loopProcessId != undefined)
        return err(`Loop detected ${loopProcessId}`);

      return getProcessId(
        targetStep.required,
        requiredGroups,
        stackedProcessIds_,
      );
    }
    return ok(true);
  };

  for (const step of recipe.steps) {
    const res = getProcessId(step.required, step.requiredGroups, []);
    if (res.success == false) return res;
  }

  return ok(true);
}
