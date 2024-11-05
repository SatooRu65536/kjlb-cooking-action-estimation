import {
  zAction,
  zActionRes,
  zActionResWithUndefined,
  zActionsRes,
  zActionsResWithUndefined,
  zCandidate,
} from "@/correction/schema/action";
import { z } from "zod";

export type Candidate = z.infer<typeof zCandidate>;
export type Action = z.infer<typeof zAction>;
export type ActionRes = z.infer<typeof zActionRes>;
export type ActionsRes = z.infer<typeof zActionsRes>;
export type ActionResWithUndefined = z.infer<typeof zActionResWithUndefined>;
export type ActionsResWithUndefined = z.infer<typeof zActionsResWithUndefined>;
