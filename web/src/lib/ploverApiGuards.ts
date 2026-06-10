import type {
    CompileDictionaryResult,
    CompileResponse,
    DeleteEntryResponse,
    DictionariesResponse,
    DictionaryEntriesPagination,
    DictionaryEntriesResponse,
    DictionaryEntrySummary,
    DictionaryStats,
    DictionarySummary,
    LookupBreakdown,
    LookupBreakdownStep,
    LookupBreakdownTransition,
    PloverStatusResponse,
    SaveEntryResponse,
    TranslationBreakdown,
} from "./ploverApiTypes.js";


const HATCHERY_SERVICE_ID = "plover-hatchery";


export const getResponseError = (responseBody: unknown) => {
    if (!isRecord(responseBody) || typeof responseBody.error !== "string") {
        return null;
    }

    return responseBody.error;
};

const isRecord = (value: unknown): value is Record<string, unknown> => (
    typeof value === "object"
    && value !== null
);

export const isPloverStatusResponse = (value: unknown): value is PloverStatusResponse => (
    isRecord(value)
    && value.service === HATCHERY_SERVICE_ID
    && value.ok === true
);

const isCompileDictionaryResult = (value: unknown): value is CompileDictionaryResult => (
    isRecord(value)
);

export const isCompileResponse = (value: unknown): value is CompileResponse => (
    isRecord(value)
    && Array.isArray(value.dictionaries)
    && value.dictionaries.every(isCompileDictionaryResult)
);

const isDictionarySummary = (value: unknown): value is DictionarySummary => (
    isRecord(value)
    && typeof value.path === "string"
    && typeof value.label === "string"
);

export const isDictionariesResponse = (value: unknown): value is DictionariesResponse => (
    isRecord(value)
    && Array.isArray(value.dictionaries)
    && value.dictionaries.every(isDictionarySummary)
);

const isDictionaryStats = (value: unknown): value is DictionaryStats => (
    isRecord(value)
    && typeof value.morphemeCount === "number"
    && typeof value.entryCount === "number"
    && typeof value.definitionCount === "number"
);

const isDictionaryEntrySummary = (value: unknown): value is DictionaryEntrySummary => (
    isRecord(value)
    && typeof value.key === "string"
    && typeof value.format === "string"
    && (
        typeof value.translation === "string"
        || value.translation === null
    )
    && typeof value.definition === "string"
);

const isDictionaryEntriesPagination = (
    value: unknown,
): value is DictionaryEntriesPagination => (
    isRecord(value)
    && typeof value.offset === "number"
    && typeof value.limit === "number"
    && typeof value.totalCount === "number"
    && typeof value.returnedCount === "number"
    && typeof value.hasPrevious === "boolean"
    && typeof value.hasNext === "boolean"
    && typeof value.query === "string"
);

export const isDictionaryEntriesResponse = (
    value: unknown,
): value is DictionaryEntriesResponse => (
    isRecord(value)
    && isDictionarySummary(value.dictionary)
    && isDictionaryStats(value.stats)
    && Array.isArray(value.entries)
    && value.entries.every(isDictionaryEntrySummary)
    && isDictionaryEntriesPagination(value.pagination)
);

export const isSaveEntryResponse = (value: unknown): value is SaveEntryResponse => (
    isRecord(value)
    && isRecord(value.entry)
    && typeof value.entry.key === "string"
    && (
        value.entry.format === undefined
        || typeof value.entry.format === "string"
    )
    && typeof value.entry.translation === "string"
    && typeof value.entry.definition === "string"
    && isCompileDictionaryResult(value.compile)
);

export const isDeleteEntryResponse = (value: unknown): value is DeleteEntryResponse => (
    isRecord(value)
    && isRecord(value.entry)
    && typeof value.entry.key === "string"
    && (
        typeof value.entry.translation === "string"
        || value.entry.translation === null
    )
    && typeof value.entry.definition === "string"
    && isCompileDictionaryResult(value.compile)
);

export const isTranslationBreakdown = (value: unknown): value is TranslationBreakdown => (
    isRecord(value)
    && typeof value.entry === "string"
    && "subtrie" in value
);

const isStringArray = (value: unknown): value is string[] => (
    Array.isArray(value)
    && value.every((item) => typeof item === "string")
);

const isNumberArray = (value: unknown): value is number[] => (
    Array.isArray(value)
    && value.every((item) => typeof item === "number")
);

const isLookupBreakdownTransition = (
    value: unknown,
): value is LookupBreakdownTransition => (
    isRecord(value)
    && typeof value.key === "string"
    && (
        typeof value.cost === "number"
        || value.cost === null
    )
    && typeof value.src_node_id === "number"
    && typeof value.dst_node_id === "number"
);

const isLookupBreakdownStep = (value: unknown): value is LookupBreakdownStep => (
    isRecord(value)
    && isStringArray(value.theory_symbols)
    && typeof value.chord === "string"
    && (
        value.starts_new_stroke === undefined
        || typeof value.starts_new_stroke === "boolean"
    )
    && isNumberArray(value.nodes)
    && (
        value.transitions === undefined
        || (
            Array.isArray(value.transitions)
            && value.transitions.every(isLookupBreakdownTransition)
        )
    )
);

export const isLookupBreakdown = (value: unknown): value is LookupBreakdown => (
    isRecord(value)
    && Array.isArray(value.path)
    && value.path.every(isLookupBreakdownStep)
    && (
        value.translation === undefined
        || typeof value.translation === "string"
    )
    && (
        value.entry_id === undefined
        || typeof value.entry_id === "number"
    )
    && (
        value.translation_id === undefined
        || typeof value.translation_id === "number"
    )
    && (
        value.cost === undefined
        || typeof value.cost === "number"
    )
);
