export type CompileDictionaryResult = {
    path?: string,
    status?: string,
    [key: string]: unknown,
};

export type CompileResponse = {
    dictionaries: CompileDictionaryResult[],
    error?: string,
};

export type DictionarySummary = {
    path: string,
    label: string,
};

export type DictionaryStats = {
    morphemeCount: number,
    entryCount: number,
    definitionCount: number,
};

export type DictionaryEntrySummary = {
    key: string,
    format: string,
    translation: string | null,
    definition: string,
};

export type DictionaryEntriesPagination = {
    offset: number,
    limit: number,
    totalCount: number,
    returnedCount: number,
    hasPrevious: boolean,
    hasNext: boolean,
    query: string,
};

export type DictionariesResponse = {
    dictionaries: DictionarySummary[],
    error?: string,
};

export type SaveEntryResponse = {
    entry: {
        key: string,
        translation: string,
        definition: string,
    },
    compile: CompileDictionaryResult,
    error?: string,
};

export type DictionaryEntriesResponse = {
    dictionary: DictionarySummary,
    stats: DictionaryStats,
    entries: DictionaryEntrySummary[],
    pagination: DictionaryEntriesPagination,
    error?: string,
};

export type DeleteEntryResponse = {
    entry: {
        key: string,
        translation: string | null,
        definition: string,
    },
    compile: CompileDictionaryResult,
    error?: string,
};

export type TranslationBreakdown = {
    entry: string,
    subtrie: any,
};

export type LookupBreakdownTransition = {
    key: string,
    cost: number | null,
    src_node_id: number,
    dst_node_id: number,
};

export type LookupBreakdownStep = {
    theory_symbols: string[],
    chord: string,
    starts_new_stroke?: boolean,
    nodes: number[],
    transitions?: LookupBreakdownTransition[],
};

export type LookupBreakdown = {
    path: LookupBreakdownStep[],
    translation?: string,
    entry_id?: number,
    translation_id?: number,
    cost?: number,
};

export type PloverApiErrorKind = "connection" | "wrong-server" | "http";

type PloverApiErrorOptions = {
    kind: PloverApiErrorKind,
    message: string,
    status?: number | null,
};

export type PloverStatusResponse = {
    service: string,
    ok: boolean,
};


export class PloverApiError extends Error {
    readonly kind: PloverApiErrorKind;
    readonly status: number | null;

    constructor(options: PloverApiErrorOptions) {
        super(options.message);
        this.name = "PloverApiError";
        this.kind = options.kind;
        this.status = options.status ?? null;
    }
}
