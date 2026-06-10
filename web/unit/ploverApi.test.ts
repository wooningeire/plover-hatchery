import {
    expect,
    test,
} from "vitest";
import {
    PloverApiError,
    deletePloverEntry,
    loadLookupBreakdown,
    loadPloverDictionaryEntries,
    loadPloverDictionaries,
    savePloverEntry,
} from "../src/lib/ploverApi.js";

type FetchImplementation = typeof fetch;


const originalFetch = globalThis.fetch;

const withFetch = async (
    fetchImplementation: FetchImplementation,
    callback: () => Promise<void>,
) => {
    globalThis.fetch = fetchImplementation;

    try {
        await callback();
    } finally {
        globalThis.fetch = originalFetch;
    }
};

const jsonResponse = (value: unknown, init?: ResponseInit) => (
    new Response(JSON.stringify(value), {
        status: 200,
        ...init,
        headers: {
            "Content-Type": "application/json",
            ...init?.headers,
        },
    })
);

const expectPloverApiError = async (
    callback: () => Promise<unknown>,
    expectedKind: PloverApiError["kind"],
    expectedMessageText: string,
) => {
    try {
        await callback();
    } catch (error) {
        expect(error).toBeInstanceOf(PloverApiError);

        const apiError = error as PloverApiError;
        expect(apiError.kind).toBe(expectedKind);
        expect(apiError.message).toContain(expectedMessageText);
        return;
    }

    throw new Error("Expected promise to reject");
};


test("loadPloverDictionaries reports when local Plover is unreachable", async () => {
    await withFetch(
        () => Promise.reject(new TypeError("fetch failed")),
        async () => {
            await expectPloverApiError(
                () => loadPloverDictionaries(),
                "connection",
                "Could not reach the Hatchery API",
            );
        },
    );
});

test("loadPloverDictionaries reports when another service uses the Plover port", async () => {
    await withFetch(
        () => Promise.resolve(jsonResponse({
            ok: true,
        })),
        async () => {
            await expectPloverApiError(
                () => loadPloverDictionaries(),
                "wrong-server",
                "it is not the Hatchery API",
            );
        },
    );
});

test("loadPloverDictionaries accepts Hatchery status before reading dictionaries", async () => {
    const requestedPaths: string[] = [];

    await withFetch(
        (input) => {
            const url = String(input);
            requestedPaths.push(new URL(url).pathname);

            if (url.endsWith("/api/status")) {
                return Promise.resolve(jsonResponse({
                    service: "plover-hatchery",
                    ok: true,
                }));
            }

            return Promise.resolve(jsonResponse({
                dictionaries: [
                    {
                        path: "user.hatchery",
                        label: "user.hatchery",
                    },
                ],
            }));
        },
        async () => {
            const response = await loadPloverDictionaries();

            expect(requestedPaths).toEqual([
                "/api/status",
                "/api/dictionaries",
            ]);
            expect(response.dictionaries).toHaveLength(1);
            expect(response.dictionaries[0]?.path).toBe("user.hatchery");
        },
    );
});

test("loadPloverDictionaryEntries reads selected dictionary entries", async () => {
    await withFetch(
        (input) => {
            const url = new URL(String(input));

            expect(url.pathname).toBe("/api/entries");
            expect(url.searchParams.get("dictionaryPath")).toBe("user.hatchery");
            expect(url.searchParams.get("offset")).toBe("25");
            expect(url.searchParams.get("limit")).toBe("50");
            expect(url.searchParams.get("query")).toBe("cat");
            expect(url.searchParams.get("resolveTranslations")).toBe("true");

            return Promise.resolve(jsonResponse({
                dictionary: {
                    path: "user.hatchery",
                    label: "user.hatchery",
                },
                stats: {
                    morphemeCount: 1,
                    entryCount: 1,
                    definitionCount: 2,
                },
                entries: [
                    {
                        key: "cat",
                        format: "sophemes",
                        translation: "cat",
                        definition: "{@k} a.a t.t",
                    },
                ],
                pagination: {
                    offset: 25,
                    limit: 50,
                    totalCount: 90,
                    returnedCount: 1,
                    hasPrevious: true,
                    hasNext: true,
                    query: "cat",
                },
            }));
        },
        async () => {
            const response = await loadPloverDictionaryEntries("user.hatchery", {
                offset: 25,
                limit: 50,
                query: "cat",
                resolveTranslations: true,
            });

            expect(response.stats.entryCount).toBe(1);
            expect(response.entries[0]?.key).toBe("cat");
            expect(response.entries[0]?.format).toBe("sophemes");
            expect(response.pagination.totalCount).toBe(90);
        },
    );
});

test("loadLookupBreakdown checks Hatchery identity before reading lookup data", async () => {
    const requestedPaths: string[] = [];

    await withFetch(
        (input) => {
            const url = new URL(String(input));
            requestedPaths.push(url.pathname);

            if (url.pathname === "/api/status") {
                return Promise.resolve(jsonResponse({
                    service: "plover-hatchery",
                    ok: true,
                }));
            }

            expect(url.pathname).toBe("/api/breakdown_lookup/APL%20%5ETPEU");
            return Promise.resolve(jsonResponse([
                {
                    path: [
                        {
                            chord: "A",
                            nodes: [0, 1],
                            theory_symbols: ["A"],
                        },
                    ],
                },
            ]));
        },
        async () => {
            const response = await loadLookupBreakdown("APL/^TPEU");

            expect(requestedPaths).toEqual([
                "/api/status",
                "/api/breakdown_lookup/APL%20%5ETPEU",
            ]);
            expect(response).toHaveLength(1);
        },
    );
});

test("loadLookupBreakdown reports Hatchery JSON endpoint errors as HTTP errors", async () => {
    await withFetch(
        (input) => {
            const url = new URL(String(input));

            if (url.pathname === "/api/status") {
                return Promise.resolve(jsonResponse({
                    service: "plover-hatchery",
                    ok: true,
                }));
            }

            return Promise.resolve(jsonResponse({
                error: "Lookup failed",
            }, {
                status: 500,
            }));
        },
        async () => {
            await expectPloverApiError(
                () => loadLookupBreakdown("APL/^TPEU"),
                "http",
                "Lookup failed",
            );
        },
    );
});

test("loadLookupBreakdown reports non-JSON Hatchery endpoint failures as HTTP errors", async () => {
    await withFetch(
        (input) => {
            const url = new URL(String(input));

            if (url.pathname === "/api/status") {
                return Promise.resolve(jsonResponse({
                    service: "plover-hatchery",
                    ok: true,
                }));
            }

            return Promise.resolve(new Response("<!doctype html>Internal Server Error", {
                status: 500,
                headers: {
                    "Content-Type": "text/html",
                },
            }));
        },
        async () => {
            await expectPloverApiError(
                () => loadLookupBreakdown("APL/^TPEU"),
                "http",
                "did not return JSON",
            );
        },
    );
});

test("savePloverEntry sends selected entry format", async () => {
    await withFetch(
        (_input, init) => {
            expect(init).toBeDefined();
            expect(init?.method).toBe("POST");
            expect(typeof init?.body).toBe("string");

            const requestBody = JSON.parse(init?.body as string);
            expect(requestBody.dictionaryPath).toBe("user.hatchery");
            expect(requestBody.translation).toBe("hang");
            expect(requestBody.definition).toBe("H A NG");
            expect(requestBody.format).toBe("theory-symbols");

            return Promise.resolve(jsonResponse({
                entry: {
                    key: "hang",
                    format: "theory-symbols",
                    translation: "hang",
                    definition: "H A NG",
                },
                compile: {
                    path: "user.hatchery",
                    status: "compiled",
                },
            }));
        },
        async () => {
            const response = await savePloverEntry(
                "user.hatchery",
                "hang",
                "H A NG",
                "theory-symbols",
            );

            expect(response.entry.format).toBe("theory-symbols");
            expect(response.compile.status).toBe("compiled");
        },
    );
});

test("deletePloverEntry deletes selected dictionary entry", async () => {
    await withFetch(
        (_input, init) => {
            expect(init).toBeDefined();
            expect(init?.method).toBe("DELETE");
            expect(typeof init?.body).toBe("string");

            const requestBody = JSON.parse(init?.body as string);
            expect(requestBody.dictionaryPath).toBe("user.hatchery");
            expect(requestBody.entryKey).toBe("cat");

            return Promise.resolve(jsonResponse({
                entry: {
                    key: "cat",
                    translation: "cat",
                    definition: "{@k} a.a t.t",
                },
                compile: {
                    path: "user.hatchery",
                    status: "compiled",
                },
            }));
        },
        async () => {
            const response = await deletePloverEntry("user.hatchery", "cat");

            expect(response.entry.key).toBe("cat");
            expect(response.compile.status).toBe("compiled");
        },
    );
});
