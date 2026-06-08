const PLOVER_API_PORT = 5325;
const HATCHERY_SERVICE_ID = "plover-hatchery";


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

type PloverStatusResponse = {
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


export const ploverApiBaseUrl = () => {
    if (typeof window === "undefined") {
        return `http://localhost:${PLOVER_API_PORT}`;
    }

    const host = window.location.hostname === "127.0.0.1"
        ? "127.0.0.1"
        : "localhost";

    return `http://${host}:${PLOVER_API_PORT}`;
};

export const checkPloverApi = async () => {
    const baseUrl = ploverApiBaseUrl();

    try {
        const responseBody = await fetchPloverJson<unknown>("/api/status");

        if (!isPloverStatusResponse(responseBody)) {
            throw createWrongServerError(baseUrl);
        }
    } catch (error) {
        if (error instanceof PloverApiError && error.kind === "http") {
            throw createWrongServerError(baseUrl);
        }

        throw error;
    }
};

export const loadPloverDictionaries = async () => {
    await checkPloverApi();

    const responseBody = await fetchPloverJson<unknown>("/api/dictionaries");
    if (!isDictionariesResponse(responseBody)) {
        throw createWrongServerError(ploverApiBaseUrl());
    }

    return responseBody;
};

export type LoadDictionaryEntriesOptions = {
    offset?: number,
    limit?: number,
    query?: string,
    resolveTranslations?: boolean,
};

export const loadPloverDictionaryEntries = async (
    dictionaryPath: string,
    options: LoadDictionaryEntriesOptions = {},
) => {
    const searchParams = new URLSearchParams({
        dictionaryPath,
    });
    searchParams.set("offset", String(options.offset ?? 0));
    searchParams.set("limit", String(options.limit ?? 100));

    if (options.query !== undefined && options.query !== "") {
        searchParams.set("query", options.query);
    }

    if (options.resolveTranslations === true) {
        searchParams.set("resolveTranslations", "true");
    }

    const responseBody = await fetchPloverJson<unknown>(`/api/entries?${searchParams}`);

    if (!isDictionaryEntriesResponse(responseBody)) {
        throw createWrongServerError(ploverApiBaseUrl());
    }

    return responseBody;
};

export const compilePloverTheory = async (refreshCache: boolean) => {
    const responseBody = await fetchPloverJson<unknown>("/api/compile", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ refreshCache }),
    });

    if (!isCompileResponse(responseBody)) {
        throw createWrongServerError(ploverApiBaseUrl());
    }

    return responseBody;
};

export const savePloverEntry = async (
    dictionaryPath: string,
    translation: string,
    definition: string,
) => {
    const responseBody = await fetchPloverJson<unknown>("/api/entries", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            dictionaryPath,
            translation,
            definition,
        }),
    });

    if (!isSaveEntryResponse(responseBody)) {
        throw createWrongServerError(ploverApiBaseUrl());
    }

    return responseBody;
};

export const deletePloverEntry = async (
    dictionaryPath: string,
    entryKey: string,
) => {
    const responseBody = await fetchPloverJson<unknown>("/api/entries", {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            dictionaryPath,
            entryKey,
        }),
    });

    if (!isDeleteEntryResponse(responseBody)) {
        throw createWrongServerError(ploverApiBaseUrl());
    }

    return responseBody;
};

export const loadTranslationBreakdown = async (translationText: string) => {
    await checkPloverApi();

    const responseBody = await fetchPloverJson<unknown>(
        `/api/breakdown_translation/${encodeURIComponent(translationText)}`,
    );

    return Array.isArray(responseBody)
        ? responseBody.filter(isTranslationBreakdown)
        : [];
};

export const loadLookupBreakdown = async (outline: string) => {
    await checkPloverApi();

    const responseBody = await fetchPloverJson<unknown>(
        `/api/breakdown_lookup/${encodeURIComponent(outline.replaceAll("/", " "))}`,
    );

    return Array.isArray(responseBody)
        ? responseBody.filter(isLookupBreakdown)
        : [];
};

const fetchPloverJson = async <T>(path: string, init?: RequestInit): Promise<T> => {
    const baseUrl = ploverApiBaseUrl();
    const response = await fetchPloverResponse(path, init, baseUrl);
    const responseBody = await parseJsonResponse(response, baseUrl);

    if (!response.ok) {
        throw new PloverApiError({
            kind: "http",
            message: getResponseError(responseBody)
                ?? `Hatchery request failed with HTTP ${response.status}`,
            status: response.status,
        });
    }

    return responseBody as T;
};

const fetchPloverResponse = async (
    path: string,
    init: RequestInit | undefined,
    baseUrl: string,
) => {
    try {
        return await fetch(`${baseUrl}${path}`, init);
    } catch {
        throw new PloverApiError({
            kind: "connection",
            message: `Could not reach the Hatchery API at ${baseUrl}. Start Plover with the Hatchery web server extension enabled. If Plover is running, another app may be using port ${PLOVER_API_PORT}.`,
        });
    }
};

const parseJsonResponse = async (response: Response, baseUrl: string) => {
    const responseText = await response.text();
    if (responseText.trim() === "") {
        return null;
    }

    try {
        return JSON.parse(responseText) as unknown;
    } catch {
        if (!response.ok) {
            throw new PloverApiError({
                kind: "http",
                message: `Hatchery request failed with HTTP ${response.status} and did not return JSON.`,
                status: response.status,
            });
        }

        throw createWrongServerError(baseUrl);
    }
};

const createWrongServerError = (baseUrl: string) => new PloverApiError({
    kind: "wrong-server",
    message: `Something responded at ${baseUrl}, but it is not the Hatchery API. Close the other app using port ${PLOVER_API_PORT}, then restart Plover's Hatchery web server extension.`,
});

const getResponseError = (responseBody: unknown) => {
    if (!isRecord(responseBody) || typeof responseBody.error !== "string") {
        return null;
    }

    return responseBody.error;
};

const isRecord = (value: unknown): value is Record<string, unknown> => (
    typeof value === "object"
    && value !== null
);

const isPloverStatusResponse = (value: unknown): value is PloverStatusResponse => (
    isRecord(value)
    && value.service === HATCHERY_SERVICE_ID
    && value.ok === true
);

const isCompileDictionaryResult = (value: unknown): value is CompileDictionaryResult => (
    isRecord(value)
);

const isCompileResponse = (value: unknown): value is CompileResponse => (
    isRecord(value)
    && Array.isArray(value.dictionaries)
    && value.dictionaries.every(isCompileDictionaryResult)
);

const isDictionarySummary = (value: unknown): value is DictionarySummary => (
    isRecord(value)
    && typeof value.path === "string"
    && typeof value.label === "string"
);

const isDictionariesResponse = (value: unknown): value is DictionariesResponse => (
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
    && (
        typeof value.translation === "string"
        || value.translation === null
    )
    && typeof value.definition === "string"
);

const isDictionaryEntriesPagination = (value: unknown): value is DictionaryEntriesPagination => (
    isRecord(value)
    && typeof value.offset === "number"
    && typeof value.limit === "number"
    && typeof value.totalCount === "number"
    && typeof value.returnedCount === "number"
    && typeof value.hasPrevious === "boolean"
    && typeof value.hasNext === "boolean"
    && typeof value.query === "string"
);

const isDictionaryEntriesResponse = (value: unknown): value is DictionaryEntriesResponse => (
    isRecord(value)
    && isDictionarySummary(value.dictionary)
    && isDictionaryStats(value.stats)
    && Array.isArray(value.entries)
    && value.entries.every(isDictionaryEntrySummary)
    && isDictionaryEntriesPagination(value.pagination)
);

const isSaveEntryResponse = (value: unknown): value is SaveEntryResponse => (
    isRecord(value)
    && isRecord(value.entry)
    && typeof value.entry.key === "string"
    && typeof value.entry.translation === "string"
    && typeof value.entry.definition === "string"
    && isCompileDictionaryResult(value.compile)
);

const isDeleteEntryResponse = (value: unknown): value is DeleteEntryResponse => (
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

const isTranslationBreakdown = (value: unknown): value is TranslationBreakdown => (
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

const isLookupBreakdownTransition = (value: unknown): value is LookupBreakdownTransition => (
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

const isLookupBreakdown = (value: unknown): value is LookupBreakdown => (
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
