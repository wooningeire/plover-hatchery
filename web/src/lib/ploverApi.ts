import {
    getResponseError,
    isCompileResponse,
    isDeleteEntryResponse,
    isDictionariesResponse,
    isDictionaryEntriesResponse,
    isLookupBreakdown,
    isPloverStatusResponse,
    isSaveEntryResponse,
    isTranslationBreakdown,
} from "./ploverApiGuards.js";
import {
    PloverApiError,
    type CompileResponse,
    type DeleteEntryResponse,
    type SaveEntryResponse,
} from "./ploverApiTypes.js";

export {
    PloverApiError,
};

export type {
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
    PloverApiErrorKind,
    SaveEntryResponse,
    TranslationBreakdown,
} from "./ploverApiTypes.js";


const PLOVER_API_PORT = 5325;


export type LoadDictionaryEntriesOptions = {
    offset?: number,
    limit?: number,
    query?: string,
    resolveTranslations?: boolean,
};

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

export const compilePloverTheory = async (refreshCache: boolean): Promise<CompileResponse> => {
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
): Promise<SaveEntryResponse> => {
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
): Promise<DeleteEntryResponse> => {
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
