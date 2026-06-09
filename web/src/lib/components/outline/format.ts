import type {
    LookupBreakdown,
    LookupBreakdownStep,
    LookupBreakdownTransition,
} from "$lib/ploverApi";


export const formatCost = (cost: number | null | undefined) => {
    if (typeof cost !== "number" || !Number.isFinite(cost)) {
        return "n/a";
    }

    return cost.toFixed(Number.isInteger(cost) ? 1 : 2);
};

export const formatResultTitle = (result: LookupBreakdown) => (
    result.translation ?? "Unknown translation"
);

export const formatEntryId = (result: LookupBreakdown) => {
    const entryId = result.entry_id ?? result.translation_id;
    return typeof entryId === "number"
        ? `#${entryId}`
        : "n/a";
};

export const stepTransitions = (step: LookupBreakdownStep) => (
    step.transitions ?? []
);

export const transitionLabel = (transition: LookupBreakdownTransition) => (
    `${transition.src_node_id} -> ${transition.dst_node_id}`
);
