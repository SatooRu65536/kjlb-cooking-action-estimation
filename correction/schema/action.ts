import { z } from "zod";
import { zProcessId, zStep } from "./recipe";

export const zCandidate = z
  .object({
    probability: z.number().min(0).max(1),
    label: z.number(),
    processId: zProcessId,
  })
  .strict();

export const zAction = z
  .object({
    start: z.number(),
    end: z.number(),
    candidates: z.array(zCandidate),
  })
  .strict();

export const zActionRes = z
  .object({
    start: z.number(),
    end: z.number(),
    step: zStep,
  })
  .strict();
export const zActionsRes = z.array(zActionRes);
export const zActionResWithUndefined = zActionRes.merge(
  z.object({ step: zStep.optional() }),
);
export const zActionsResWithUndefined = z.array(zActionResWithUndefined);
